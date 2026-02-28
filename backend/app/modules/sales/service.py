from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.inventory.repository import inventory_repository
from app.modules.inventory.schemas import StockMovementCreateSchema
from app.modules.products.repository import product_repository
from app.modules.sales.repository import sales_repository
from app.modules.sales.schemas import SaleCreateSchema, SaleItemResponseSchema, SaleListResponseSchema, SaleResponseSchema
from app.workers.celery_app import celery_app


class SalesService:
    def create_sale(
        self,
        db: Session,
        payload: SaleCreateSchema,
        shop_id: str,
        correlation_id: str,
    ) -> SaleResponseSchema:
        total = 0.0
        enriched_items: list[dict] = []

        for item in payload.items:
            product = product_repository.get_by_id(db, item.product_id, shop_id)
            if not product or not product.is_active:
                raise ValidationException(f"Product {item.product_id} is not available in your shop.")
            available = inventory_repository.total_quantity(db, shop_id, item.product_id)
            if item.quantity > available:
                raise ValidationException(f"Insufficient stock for product {product.sku}.")

            unit_price = float(product.price)
            line_total = unit_price * item.quantity
            total += line_total
            enriched_items.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )

        sale_number = f"SRIP-{datetime.now(UTC).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        sale = sales_repository.create_sale(db, shop_id, sale_number, round(total, 2))
        sale_items = []
        for entry in enriched_items:
            sale_item = sales_repository.add_sale_item(db, sale.id, **entry)
            sale_items.append(sale_item)
            inventory_repository.consume_stock(db, shop_id, entry["product_id"], entry["quantity"])
            inventory_repository.create_stock_movement(
                db,
                StockMovementCreateSchema(
                    product_id=entry["product_id"],
                    batch_id="auto-fefo-sale",
                    movement_type="out",
                    quantity=entry["quantity"],
                    reason=f"sale:{sale_number}",
                ),
                shop_id,
                autocommit=False,
            )
        db.commit()
        db.refresh(sale)

        celery_app.send_task(
            "app.workers.tasks.analytics.ingest_sale_event",
            kwargs={
                "sale_id": sale.id,
                "shop_id": shop_id,
                "correlation_id": correlation_id,
            },
        )
        celery_app.send_task("app.workers.tasks.reports.generate_daily_report", kwargs={"shop_id": shop_id})
        celery_app.send_task("app.workers.tasks.stock_alerts.check_low_stock", kwargs={"shop_id": shop_id})

        return SaleResponseSchema(
            id=sale.id,
            shop_id=sale.shop_id,
            sale_number=sale.sale_number,
            total_amount=sale.total_amount,
            created_at=sale.created_at,
            items=[SaleItemResponseSchema.model_validate(item) for item in sale_items],
        )

    def get_sale(self, db: Session, shop_id: str, sale_id: str) -> SaleResponseSchema:
        sale = sales_repository.get_sale(db, shop_id, sale_id)
        if not sale:
            raise NotFoundException("No sale found for provided ID.")
        items = sales_repository.sale_items(db, sale.id)
        return SaleResponseSchema(
            id=sale.id,
            shop_id=sale.shop_id,
            sale_number=sale.sale_number,
            total_amount=sale.total_amount,
            created_at=sale.created_at,
            items=[SaleItemResponseSchema.model_validate(i) for i in items],
        )

    def list_sales(
        self,
        db: Session,
        shop_id: str,
        skip: int = 0,
        limit: int = 20,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> SaleListResponseSchema:
        if from_date and to_date and from_date > to_date:
            raise ValidationException("From date cannot be after To date.")
        sales, total = sales_repository.list_sales(db, shop_id, skip, limit, from_date, to_date)
        response_items: list[SaleResponseSchema] = []
        for sale in sales:
            sale_items = sales_repository.sale_items(db, sale.id)
            response_items.append(
                SaleResponseSchema(
                    id=sale.id,
                    shop_id=sale.shop_id,
                    sale_number=sale.sale_number,
                    total_amount=sale.total_amount,
                    created_at=sale.created_at,
                    items=[SaleItemResponseSchema.model_validate(i) for i in sale_items],
                )
            )
        return SaleListResponseSchema(items=response_items, total=total, skip=skip, limit=limit)


sales_service = SalesService()
