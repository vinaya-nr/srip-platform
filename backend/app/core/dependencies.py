from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthorizationException
from app.core.security import TokenPayload, verify_token
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.users.repository import user_repository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUserSchema:
    token_payload: TokenPayload = verify_token(token)
    if not token_payload.shop_id:
        raise AuthorizationException("Token shop context missing.", status_code=401)
    user = user_repository.get_user_by_id(db, token_payload.sub, token_payload.shop_id)
    if not user:
        raise AuthorizationException("User not found for token context.", status_code=401)
    if not user.is_active:
        raise AuthorizationException("User is inactive.", status_code=401)

    return CurrentUserSchema(
        id=str(user.id),
        email=user.email,
        shop_id=str(user.shop_id),
    )


def get_current_shop(current_user: Annotated[CurrentUserSchema, Depends(get_current_user)]) -> str:
    return current_user.shop_id
