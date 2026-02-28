from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.notifications.repository import notification_repository
from app.modules.notifications.schemas import (
    NotificationCreateSchema,
    NotificationListResponseSchema,
    NotificationResponseSchema,
)


class NotificationService:
    def create(
        self,
        db: Session,
        shop_id: str,
        payload: NotificationCreateSchema,
    ) -> NotificationResponseSchema:
        notification = notification_repository.create(db, shop_id, payload)
        return NotificationResponseSchema.model_validate(notification)

    def list(
        self,
        db: Session,
        shop_id: str,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> NotificationListResponseSchema:
        if from_date and to_date and from_date > to_date:
            raise ValidationException("from_date cannot be after to_date.")

        notifications, total = notification_repository.list(
            db,
            shop_id,
            unread_only,
            skip,
            limit,
            from_date,
            to_date,
        )
        return NotificationListResponseSchema(
            items=[NotificationResponseSchema.model_validate(n) for n in notifications],
            total=total,
            skip=skip,
            limit=limit,
        )

    def mark_read(self, db: Session, shop_id: str, notification_id: str) -> NotificationResponseSchema:
        notification = notification_repository.get(db, shop_id, notification_id)
        if not notification:
            raise NotFoundException("Notification not found.")
        updated = notification_repository.mark_read(db, notification)
        return NotificationResponseSchema.model_validate(updated)


notification_service = NotificationService()
