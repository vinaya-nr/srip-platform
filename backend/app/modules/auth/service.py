from datetime import UTC, datetime

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthorizationException
from app.core.security import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token_unsafe,
    get_redis_client,
    verify_password,
)
from app.modules.auth.repository import auth_repository
from app.modules.auth.schemas import CurrentUserSchema, LoginSchema, TokenResponseSchema
from app.modules.users.repository import user_repository


class AuthService:
    def login(
        self,
        db: Session,
        payload: LoginSchema,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[TokenResponseSchema, str]:
        user = user_repository.get_user_by_email(db, payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AuthorizationException("Invalid email or password.", status_code=401)
        if not user.is_active:
            raise AuthorizationException("User account is inactive.", status_code=401)

        access_token = create_access_token(str(user.id), str(user.shop_id))
        refresh_token = create_refresh_token(str(user.id))
        refresh_claims = decode_token_unsafe(refresh_token) or {}
        if not refresh_claims.get("jti") or not refresh_claims.get("exp"):
            raise AuthorizationException("Failed to create refresh session.", status_code=500)
        auth_repository.create_refresh_session(
            db,
            jti=str(refresh_claims.get("jti")),
            user_id=str(user.id),
            expires_at_epoch=int(refresh_claims.get("exp", 0)),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.commit()

        user = CurrentUserSchema(
            id=str(user.id),
            email=user.email,
            shop_id=str(user.shop_id),
        )
        response = TokenResponseSchema(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user,
        )
        return response, refresh_token

    def refresh(
        self,
        db: Session,
        refresh_token: str | None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[TokenResponseSchema, str]:
        if not refresh_token:
            raise AuthorizationException("Refresh token is missing.", status_code=401)

        try:
            decoded = jwt.decode(
                refresh_token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError:
            raise AuthorizationException("Invalid refresh token.", status_code=401)

        if decoded.get("token_type") != "refresh":
            raise AuthorizationException("Invalid refresh token type.", status_code=401)

        claims_unsafe = decode_token_unsafe(refresh_token)
        if not claims_unsafe:
            raise AuthorizationException("Invalid refresh token payload.", status_code=401)

        user_id = str(claims_unsafe.get("sub"))
        jti = str(claims_unsafe.get("jti"))
        exp = int(claims_unsafe.get("exp", 0))
        if not user_id or not jti:
            raise AuthorizationException("Refresh token payload incomplete.", status_code=401)

        redis_client = get_redis_client()
        if not redis_client.exists(f"refresh:{jti}"):
            raise AuthorizationException("Refresh token is revoked or expired.", status_code=401)

        session_row = auth_repository.get_refresh_session(db, jti)
        if not session_row:
            raise AuthorizationException("Refresh token session not found.", status_code=401)
        if session_row["revoked_at"] is not None:
            auth_repository.revoke_all_user_sessions(db, user_id)
            db.commit()
            raise AuthorizationException("Refresh token replay detected. All sessions revoked.", status_code=401)

        user = user_repository.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise AuthorizationException("User not available for token refresh.", status_code=401)

        ttl = max(1, exp - int(datetime.now(UTC).timestamp()))
        blacklist_token(jti, ttl)
        redis_client.delete(f"refresh:{jti}")

        access_token = create_access_token(str(user.id), str(user.shop_id))
        new_refresh_token = create_refresh_token(str(user.id))
        new_refresh_claims = decode_token_unsafe(new_refresh_token) or {}
        if not new_refresh_claims.get("jti") or not new_refresh_claims.get("exp"):
            raise AuthorizationException("Failed to rotate refresh session.", status_code=500)
        auth_repository.create_refresh_session(
            db,
            jti=str(new_refresh_claims.get("jti")),
            user_id=str(user.id),
            expires_at_epoch=int(new_refresh_claims.get("exp", 0)),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        auth_repository.revoke_refresh_session(db, jti, replaced_by_jti=str(new_refresh_claims.get("jti")))
        db.commit()

        current_user = CurrentUserSchema(
            id=str(user.id),
            email=user.email,
            shop_id=str(user.shop_id),
        )
        return (
            TokenResponseSchema(
                access_token=access_token,
                expires_in=settings.access_token_expire_minutes * 60,
                user=current_user,
            ),
            new_refresh_token,
        )

    def logout(self, db: Session, access_token: str | None, refresh_token: str | None) -> None:
        now_epoch = int(datetime.now(UTC).timestamp())
        for token in [access_token, refresh_token]:
            if not token:
                continue
            claims = decode_token_unsafe(token)
            if not claims:
                continue
            jti = claims.get("jti")
            exp = int(claims.get("exp", now_epoch))
            if jti:
                blacklist_token(str(jti), max(1, exp - now_epoch))
                get_redis_client().delete(f"refresh:{jti}")
                auth_repository.revoke_refresh_session(db, str(jti))
        db.commit()


auth_service = AuthService()
