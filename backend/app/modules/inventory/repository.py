from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.inventory.models import Batch, StockMovement
from app.modules.inventory.schemas import BatchCreateSchema, BatchMetadataUpdateSchema, StockMovementCreateSchema


class InventoryRepository:
    def get_batch(self, db: Session, shop_id: str, batch_id: str) -> Batch | None:
        return db.scalar(select(Batch).where(Batch.shop_id == shop_id, Batch.id == batch_id))

    def create_batch(self, db: Session, payload: BatchCreateSchema, shop_id: str) -> Batch:
        batch = Batch(shop_id=shop_id, **payload.model_dump())
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch

    def update_batch_metadata(self, db: Session, batch: Batch, payload: BatchMetadataUpdateSchema) -> Batch:
        for key, value in payload.model_dump().items():
            setattr(batch, key, value)
        db.commit()
        db.refresh(batch)
        return batch

    def list_batches(
        self,
        db: Session,
        shop_id: str,
        product_id: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Batch], int]:
        stmt = select(Batch).where(Batch.shop_id == shop_id)
        if product_id:
            stmt = stmt.where(Batch.product_id == product_id)

        total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        paginated_stmt = stmt.order_by(Batch.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(paginated_stmt).all()), total

    def expiring_batches(self, db: Session, shop_id: str, within_days: int = 15) -> list[Batch]:
        boundary = date.today() + timedelta(days=within_days)
        stmt = (
            select(Batch)
            .where(Batch.shop_id == shop_id, Batch.expiry_date.is_not(None), Batch.expiry_date <= boundary)
            .order_by(Batch.expiry_date.asc())
        )
        return list(db.scalars(stmt).all())

    def create_stock_movement(
        self,
        db: Session,
        payload: StockMovementCreateSchema,
        shop_id: str,
        autocommit: bool = True,
    ) -> StockMovement:
        movement = StockMovement(
            shop_id=shop_id,
            product_id=payload.product_id,
            movement_type=payload.movement_type,
            quantity=payload.quantity,
            reason=payload.reason,
        )
        db.add(movement)
        if autocommit:
            db.commit()
            db.refresh(movement)
        return movement

    def consume_stock(self, db: Session, shop_id: str, product_id: str, quantity: int) -> None:
        remaining = quantity
        batches = list(
            db.scalars(
                select(Batch)
                .where(Batch.shop_id == shop_id, Batch.product_id == product_id, Batch.quantity > 0)
                .order_by(Batch.expiry_date.asc().nulls_last(), Batch.created_at.asc())
            ).all()
        )
        for batch in batches:
            if remaining <= 0:
                break
            deduction = min(batch.quantity, remaining)
            batch.quantity -= deduction
            remaining -= deduction
        if remaining > 0:
            raise ValueError("insufficient_stock_batches")

    def increase_stock(
        self,
        db: Session,
        shop_id: str,
        product_id: str,
        quantity: int,
        unit_cost: float | None = None,
        expiry_date: date | None = None,
    ) -> Batch:
        batch = Batch(
            shop_id=shop_id,
            product_id=product_id,
            quantity=quantity,
            unit_cost=unit_cost,
            expiry_date=expiry_date,
        )
        db.add(batch)
        return batch

    def total_quantity(self, db: Session, shop_id: str, product_id: str) -> int:
        batches = db.scalars(
            select(Batch).where(Batch.shop_id == shop_id, Batch.product_id == product_id)
        ).all()
        return sum(b.quantity for b in batches)


inventory_repository = InventoryRepository()
