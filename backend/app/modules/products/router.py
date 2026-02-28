from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.products.schemas import (
    ProductCreateSchema,
    ProductFilterSchema,
    ProductListResponseSchema,
    ProductResponseSchema,
    ProductStockResponseSchema,
    ProductUpdateSchema,
)
from app.modules.products.service import product_service

router = APIRouter()


@router.post("", response_model=ProductResponseSchema, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> ProductResponseSchema:
    return product_service.create_product(db, payload, current_user.shop_id)


@router.get("", response_model=ProductListResponseSchema)
def list_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    category_id: str | None = None,
    search: str | None = None,
    is_active: bool | None = True,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> ProductListResponseSchema:
    filters = ProductFilterSchema(category_id=category_id, search=search, is_active=is_active)
    return product_service.list_products(db, current_user.shop_id, filters, skip, limit)


@router.get("/{product_id}/stock", response_model=ProductStockResponseSchema)
def get_product_stock(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> ProductStockResponseSchema:
    return product_service.get_product_stock(db, product_id, current_user.shop_id)


@router.get("/{product_id}", response_model=ProductResponseSchema)
def get_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> ProductResponseSchema:
    return product_service.get_product(db, product_id, current_user.shop_id)


@router.patch("/{product_id}", response_model=ProductResponseSchema)
def update_product(
    product_id: str,
    payload: ProductUpdateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> ProductResponseSchema:
    return product_service.update_product(db, product_id, payload, current_user.shop_id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> Response:
    product_service.delete_product(db, product_id, current_user.shop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
