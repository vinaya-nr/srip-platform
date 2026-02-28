from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.products.models import Category, Product
from app.modules.products.schemas import ProductCreateSchema, ProductFilterSchema, ProductUpdateSchema


class ProductRepository:
    def get_by_id(self, db: Session, product_id: str, shop_id: str) -> Product | None:
        return db.scalar(
            select(Product).where(Product.id == product_id, Product.shop_id == shop_id)
        )

    def get_by_sku(self, db: Session, sku: str, shop_id: str) -> Product | None:
        return db.scalar(select(Product).where(Product.sku == sku, Product.shop_id == shop_id))

    def category_exists(self, db: Session, category_id: str, shop_id: str) -> bool:
        return bool(db.scalar(select(Category.id).where(Category.id == category_id, Category.shop_id == shop_id)))

    def create(self, db: Session, payload: ProductCreateSchema, shop_id: str) -> Product:
        product = Product(shop_id=shop_id, **payload.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def update(self, db: Session, product: Product, payload: ProductUpdateSchema) -> Product:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, key, value)
        db.commit()
        db.refresh(product)
        return product

    def delete(self, db: Session, product: Product) -> None:
        db.delete(product)
        db.commit()

    def list(
        self,
        db: Session,
        shop_id: str,
        filters: ProductFilterSchema,
        skip: int,
        limit: int,
    ) -> tuple[list[Product], int]:
        stmt: Select[tuple[Product]] = select(Product).where(Product.shop_id == shop_id)
        if filters.category_id:
            stmt = stmt.where(Product.category_id == filters.category_id)
        if filters.search:
            stmt = stmt.where(Product.name.ilike(f"%{filters.search}%"))
        if filters.is_active is not None:
            stmt = stmt.where(Product.is_active == filters.is_active)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(db.scalar(total_stmt) or 0)

        paginated_stmt = stmt.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(paginated_stmt).all()), total


product_repository = ProductRepository()
