from datetime import UTC, datetime, timedelta
from functools import lru_cache
import logging
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel
from redis import Redis

from app.core.config import settings
from app.core.exceptions import AuthorizationException

logger = logging.getLogger(__name__)


class BcryptPasswordContext:
    def __init__(self, rounds: int) -> None:
        self.rounds = rounds

    def hash(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=self.rounds)).decode("utf-8")

    def verify(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


pwd_context = BcryptPasswordContext(rounds=settings.bcrypt_rounds)


class InMemoryRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def setex(self, key: str, _: int, value: str) -> None:
        self.store[key] = value

    def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

    def delete(self, key: str) -> None:
        self.store.pop(key, None)

    def ping(self) -> bool:
        return True

    def xadd(self, _: str, __: dict, maxlen: int | None = None) -> str:  # noqa: ARG002
        return "1-0"


class TokenPayload(BaseModel):
    sub: str
    shop_id: str | None = None
    jti: str
    exp: int
    iat: int
    token_type: str


@lru_cache
def get_redis_client() -> Redis | InMemoryRedis:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        client.ping()
        return client
    except Exception:
        if settings.env.lower() == "production":
            raise
        logger.warning(
            "redis_unavailable_using_in_memory_fallback",
            extra={"extra": {"redis_url": settings.redis_url}},
        )
        return InMemoryRedis()


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def _create_token(payload: dict, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    to_encode = payload.copy()
    to_encode.update({"iat": int(now.timestamp()), "exp": int((now + expires_delta).timestamp())})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, shop_id: str) -> str:
    jti = str(uuid4())
    return _create_token(
        {"sub": str(user_id), "shop_id": str(shop_id), "jti": jti, "token_type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    jti = str(uuid4())
    ttl = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())
    token = _create_token(
        {"sub": str(user_id), "jti": jti, "token_type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )
    get_redis_client().setex(f"refresh:{jti}", ttl, str(user_id))
    return token


def blacklist_token(jti: str, ttl_seconds: int) -> None:
    get_redis_client().setex(f"blacklist:{jti}", max(1, ttl_seconds), "1")


def is_token_blacklisted(jti: str) -> bool:
    return bool(get_redis_client().exists(f"blacklist:{jti}"))


def verify_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        token_payload = TokenPayload(**payload)
    except (JWTError, ValueError):
        raise AuthorizationException("Invalid token.", status_code=401)

    if token_payload.token_type != "access":
        raise AuthorizationException("Invalid token type.", status_code=401)
    if is_token_blacklisted(token_payload.jti):
        raise AuthorizationException("Token has been revoked.", status_code=401)
    return token_payload


def decode_token_unsafe(token: str) -> dict | None:
    try:
        return jwt.get_unverified_claims(token)
    except JWTError:
        return None
