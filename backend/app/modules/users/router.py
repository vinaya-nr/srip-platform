from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.users.schemas import UserCreateSchema, UserProfileSchema, UserResponseSchema
from app.modules.users.service import user_service

router = APIRouter()


@router.post("", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreateSchema,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponseSchema:
    return user_service.create_user(db, payload)


@router.get("/me", response_model=UserProfileSchema)
def get_profile(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> UserProfileSchema:
    return user_service.get_profile(db, current_user.id, current_user.shop_id)
