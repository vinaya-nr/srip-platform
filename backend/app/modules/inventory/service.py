from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.inventory.repository import inventory_repository
from app.modules.inventory.schemas import (
    BatchListResponseSchema,
    BatchCreateSchema,
    BatchMetadataUpdateSchema,
    BatchResponseSchema,
    StockMovementCreateSchema,
    StockMovementResponseSchema,
)
from app.modules.products.repository import product_repository
from app.workers.celery_app import celery_app


class InventoryService:
    def create_batch(self, db: Session, payload: BatchCreateSchema, shop_id: str) -> BatchResponseSchema:
        if not product_repository.get_by_id(db, payload.product_id, shop_id):
            raise ValidationException("Product does not exist in your shop.")
        batch = inventory_repository.create_batch(db, payload, shop_id)
        return BatchResponseSchema.model_validate(batch)

    def list_batches(
        self,
        db: Session,
        shop_id: str,
        product_id: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> BatchListResponseSchema:
        batches, total = inventory_repository.list_batches(db, shop_id, product_id, skip, limit)
        return BatchListResponseSchema(
            items=[BatchResponseSchema.model_validate(batch) for batch in batches],
            total=total,
            skip=skip,
            limit=limit,
        )

    def update_batch_metadata(
        self,
        db: Session,
        batch_id: str,
        payload: BatchMetadataUpdateSchema,
        shop_id: str,
    ) -> BatchResponseSchema:
        batch = inventory_repository.get_batch(db, shop_id, batch_id)
        if not batch:
            raise NotFoundException("No batch found for provided ID.")
        updated = inventory_repository.update_batch_metadata(db, batch, payload)
        return BatchResponseSchema.model_validate(updated)

    def record_movement(
        self,
        db: Session,
        payload: StockMovementCreateSchema,
        shop_id: str,
        correlation_id: str,
    ) -> StockMovementResponseSchema:
        product = product_repository.get_by_id(db, payload.product_id, shop_id)
        if not product:
            raise ValidationException("Product does not exist in your shop.")

        batch = inventory_repository.get_batch(db, shop_id, payload.batch_id)
        if not batch:
            raise NotFoundException("No batch found for provided ID.")
        if batch.product_id != payload.product_id:
            raise ValidationException("Selected batch does not belong to selected product.")

        if payload.movement_type == "in":
            batch.quantity += payload.quantity
        elif payload.movement_type == "out":
            if payload.quantity > batch.quantity:
                raise ValidationException("Insufficient stock in selected batch for stock-out movement.")
            batch.quantity -= payload.quantity
        else:
            if not payload.adjustment_mode:
                raise ValidationException("adjustment_mode is required for adjustment movement.")
            if payload.adjustment_mode == "increase":
                batch.quantity += payload.quantity
            else:
                if payload.quantity > batch.quantity:
                    raise ValidationException("Insufficient stock in selected batch for adjustment decrease.")
                batch.quantity -= payload.quantity

        movement_reason = (
            f"batch:{payload.batch_id} | {payload.reason}"
            if payload.reason
            else f"batch:{payload.batch_id}"
        )
        movement_payload = payload.model_copy(update={"reason": movement_reason})
        movement = inventory_repository.create_stock_movement(db, movement_payload, shop_id, autocommit=False)
        db.commit()
        db.refresh(movement)
        celery_app.send_task(
            "app.workers.tasks.analytics.stream_inventory_event",
            kwargs={
                "shop_id": shop_id,
                "product_id": payload.product_id,
                "movement_type": payload.movement_type,
                "quantity": payload.quantity,
                "correlation_id": correlation_id,
            },
        )
        celery_app.send_task("app.workers.tasks.stock_alerts.check_low_stock", kwargs={"shop_id": shop_id})
        return StockMovementResponseSchema.model_validate(movement)

    def get_expiry_alerts(self, db: Session, shop_id: str, within_days: int = 15) -> list[BatchResponseSchema]:
        rows = inventory_repository.expiring_batches(db, shop_id, within_days)
        return [BatchResponseSchema.model_validate(row) for row in rows]


inventory_service = InventoryService()
