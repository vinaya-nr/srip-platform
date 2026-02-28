from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationCreateSchema


class NotificationRepository:
    def create(self, db: Session, shop_id: str, payload: NotificationCreateSchema) -> Notification:
        notification = Notification(shop_id=shop_id, **payload.model_dump())
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def list(
        self,
        db: Session,
        shop_id: str,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 20,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.shop_id == shop_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        if from_date:
            start_dt = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(Notification.created_at >= start_dt)
        if to_date:
            end_exclusive_dt = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
            stmt = stmt.where(Notification.created_at < end_exclusive_dt)

        total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        paginated_stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(paginated_stmt).all()), total

    def get(self, db: Session, shop_id: str, notification_id: str) -> Notification | None:
        return db.scalar(
            select(Notification).where(Notification.shop_id == shop_id, Notification.id == notification_id)
        )

    def mark_read(self, db: Session, notification: Notification) -> Notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification


notification_repository = NotificationRepository()
