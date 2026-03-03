from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.products.models import Product
from app.modules.sales.models import Sale, SaleItem


class SalesRepository:
    def create_sale(self, db: Session, shop_id: str, sale_number: str, total_amount: float) -> Sale:
        sale = Sale(shop_id=shop_id, sale_number=sale_number, total_amount=total_amount)
        db.add(sale)
        db.flush()
        return sale

    def add_sale_item(
        self,
        db: Session,
        sale_id: str,
        product_id: str,
        quantity: int,
        unit_price: float,
        line_total: float,
    ) -> SaleItem:
        item = SaleItem(
            sale_id=sale_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
        )
        db.add(item)
        return item

    def list_sales(
        self,
        db: Session,
        shop_id: str,
        skip: int,
        limit: int,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[Sale], int]:
        stmt = select(Sale).where(Sale.shop_id == shop_id)
        if from_date:
            from_dt = datetime.combine(from_date, time.min, tzinfo=UTC)
            stmt = stmt.where(Sale.created_at >= from_dt)
        if to_date:
            to_dt = datetime.combine(to_date, time.max, tzinfo=UTC)
            stmt = stmt.where(Sale.created_at <= to_dt)
        total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        rows = db.scalars(stmt.order_by(Sale.created_at.desc()).offset(skip).limit(limit)).all()
        return list(rows), total

    def get_sale(self, db: Session, shop_id: str, sale_id: str) -> Sale | None:
        return db.scalar(select(Sale).where(Sale.id == sale_id, Sale.shop_id == shop_id))

    def sale_items(self, db: Session, sale_id: str) -> list[SaleItem]:
        return list(db.scalars(select(SaleItem).where(SaleItem.sale_id == sale_id)).all())

    def sale_items_with_product_names(self, db: Session, shop_id: str, sale_id: str) -> list[dict]:
        rows = db.execute(
            select(
                SaleItem.product_id,
                Product.name.label("product_name"),
                SaleItem.quantity,
                SaleItem.unit_price,
                SaleItem.line_total,
            )
            .outerjoin(
                Product,
                (Product.id == SaleItem.product_id) & (Product.shop_id == shop_id),
            )
            .where(SaleItem.sale_id == sale_id)
        ).mappings()
        return [dict(row) for row in rows]


sales_repository = SalesRepository()
