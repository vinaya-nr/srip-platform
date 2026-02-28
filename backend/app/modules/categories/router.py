from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.categories.schemas import CategoryCreateSchema, CategoryResponseSchema, CategoryUpdateSchema
from app.modules.categories.service import category_service

router = APIRouter()


@router.post("", response_model=CategoryResponseSchema, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> CategoryResponseSchema:
    return category_service.create_category(db, payload, current_user.shop_id)


@router.get("", response_model=list[CategoryResponseSchema])
def list_categories(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> list[CategoryResponseSchema]:
    return category_service.list_categories(db, current_user.shop_id)


@router.get("/{category_id}", response_model=CategoryResponseSchema)
def get_category(
    category_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> CategoryResponseSchema:
    return category_service.get_category(db, category_id, current_user.shop_id)


@router.patch("/{category_id}", response_model=CategoryResponseSchema)
def update_category(
    category_id: str,
    payload: CategoryUpdateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> CategoryResponseSchema:
    return category_service.update_category(db, category_id, payload, current_user.shop_id)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> Response:
    category_service.delete_category(db, category_id, current_user.shop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
