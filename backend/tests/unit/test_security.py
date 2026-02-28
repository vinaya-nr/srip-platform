import time
import pytest

from app.core.security import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token_unsafe,
    hash_password,
    is_token_blacklisted,
    verify_password,
    verify_token,
    get_redis_client,
    InMemoryRedis,
)
from app.core.config import Settings

from ..test_conf import dummy_redis


def test_decode_token_unsafe_invalid_returns_none() -> None:
    assert decode_token_unsafe("not-a-token") is None


def test_password_hash_and_verify(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr("app.core.security.pwd_context.hash", lambda plain: f"hashed::{plain}")
    monkeypatch.setattr(
        "app.core.security.pwd_context.verify",
        lambda plain, hashed: hashed == f"hashed::{plain}",
    )
    hashed = hash_password("password-123")
    assert hashed == "hashed::password-123"
    assert verify_password("password-123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_roundtrip(dummy_redis) -> None:  # noqa: ANN001
    token = create_access_token("user-id", "shop-id")
    payload = verify_token(token)
    assert payload.sub == "user-id"
    assert payload.shop_id == "shop-id"
    assert payload.token_type == "access"


def test_blacklist_blocks_token(dummy_redis) -> None:  # noqa: ANN001
    token = create_access_token("user-id", "shop-id")
    payload = decode_token_unsafe(token)
    assert payload is not None
    jti = str(payload["jti"])
    blacklist_token(jti, 60)
    assert is_token_blacklisted(jti) is True


def test_refresh_token_is_stored(dummy_redis) -> None:  # noqa: ANN001
    token = create_refresh_token("user-id")
    payload = decode_token_unsafe(token)
    assert payload is not None
    assert payload["token_type"] == "refresh"
    assert dummy_redis.exists(f"refresh:{payload['jti']}") == 1
    assert int(payload["exp"]) > int(time.time())


def test_verify_token_errors(dummy_redis):
    # invalid string
    with pytest.raises(Exception):
        verify_token("not-a-token")

    # refresh token passed to verify_token should trigger AuthorizationException
    refresh = create_refresh_token("user-id")
    with pytest.raises(Exception):
        verify_token(refresh)

    # blacklist behaviour
    token = create_access_token("user-id", "shop-id")
    jti = str(decode_token_unsafe(token)["jti"])
    blacklist_token(jti, 1)
    with pytest.raises(Exception):
        verify_token(token)


def test_get_redis_client_fallback(monkeypatch):
    # simulate unreachable redis to exercise fallback code path
    class FakeRedis:
        @staticmethod
        def from_url(url, decode_responses=True):
            class Client:
                def ping(self):
                    raise Exception("down")
            return Client()

    from app.core import security
    monkeypatch.setattr(security, "Redis", FakeRedis)
    monkeypatch.setattr(security, "settings", Settings(env="development", redis_url="redis://x"))
    security.get_redis_client.cache_clear()
    client = security.get_redis_client()
    assert isinstance(client, InMemoryRedis)
