from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.inventory.schemas import (
    BatchCreateSchema,
    BatchListResponseSchema,
    BatchMetadataUpdateSchema,
    BatchResponseSchema,
    StockMovementCreateSchema,
    StockMovementResponseSchema,
)
from app.modules.inventory.service import inventory_service

router = APIRouter()


@router.post("/batches", response_model=BatchResponseSchema, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> BatchResponseSchema:
    return inventory_service.create_batch(db, payload, current_user.shop_id)


@router.get("/batches", response_model=BatchListResponseSchema)
def list_batches(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    product_id: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> BatchListResponseSchema:
    return inventory_service.list_batches(db, current_user.shop_id, product_id, skip, limit)


@router.patch("/batches/{batch_id}", response_model=BatchResponseSchema)
def update_batch_metadata(
    batch_id: str,
    payload: BatchMetadataUpdateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> BatchResponseSchema:
    return inventory_service.update_batch_metadata(db, batch_id, payload, current_user.shop_id)


@router.post("/movements", response_model=StockMovementResponseSchema, status_code=status.HTTP_201_CREATED)
def record_movement(
    payload: StockMovementCreateSchema,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> StockMovementResponseSchema:
    correlation_id = getattr(request.state, "correlation_id", "")
    return inventory_service.record_movement(db, payload, current_user.shop_id, correlation_id)


@router.get("/alerts/expiry", response_model=list[BatchResponseSchema])
def expiry_alerts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    within_days: int = 15,
) -> list[BatchResponseSchema]:
    return inventory_service.get_expiry_alerts(db, current_user.shop_id, within_days)
