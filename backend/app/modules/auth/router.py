from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.schemas import LoginSchema, TokenResponseSchema
from app.modules.auth.service import auth_service

router = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=settings.refresh_cookie_path,
    )


@router.post("/login", response_model=TokenResponseSchema)
def login(
    payload: LoginSchema,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponseSchema:
    token_response, refresh_token = auth_service.login(
        db,
        payload,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post("/refresh", response_model=TokenResponseSchema)
def refresh(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponseSchema:
    refresh_token = request.cookies.get("refresh_token")
    token_response, new_refresh_token = auth_service.refresh(
        db,
        refresh_token,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_refresh_cookie(response, new_refresh_token)
    return token_response


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, bool]:
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    refresh_token = request.cookies.get("refresh_token")
    auth_service.logout(db, access_token, refresh_token)
    response.delete_cookie(
        key="refresh_token",
        path=settings.refresh_cookie_path,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
    return {"success": True}
