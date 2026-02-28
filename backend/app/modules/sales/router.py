from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.sales.schemas import SaleCreateSchema, SaleListResponseSchema, SaleResponseSchema
from app.modules.sales.service import sales_service

router = APIRouter()


@router.post("", response_model=SaleResponseSchema, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreateSchema,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> SaleResponseSchema:
    correlation_id = getattr(request.state, "correlation_id", "")
    return sales_service.create_sale(db, payload, current_user.shop_id, correlation_id)


@router.get("/{sale_id}", response_model=SaleResponseSchema)
def get_sale(
    sale_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> SaleResponseSchema:
    return sales_service.get_sale(db, current_user.shop_id, sale_id)


@router.get("", response_model=SaleListResponseSchema)
def list_sales(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
) -> SaleListResponseSchema:
    return sales_service.list_sales(db, current_user.shop_id, skip, limit, from_date, to_date)
