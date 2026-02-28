from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.notifications.schemas import (
    NotificationCreateSchema,
    NotificationListResponseSchema,
    NotificationResponseSchema,
)
from app.modules.notifications.service import notification_service

router = APIRouter()


@router.post("", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> NotificationResponseSchema:
    return notification_service.create(db, current_user.shop_id, payload)


@router.get("", response_model=NotificationListResponseSchema)
def list_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    unread_only: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
) -> NotificationListResponseSchema:
    return notification_service.list(
        db,
        current_user.shop_id,
        unread_only,
        skip,
        limit,
        from_date,
        to_date,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponseSchema)
def mark_notification_as_read(
    notification_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> NotificationResponseSchema:
    return notification_service.mark_read(db, current_user.shop_id, notification_id)
