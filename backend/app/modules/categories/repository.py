from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreateSchema, CategoryUpdateSchema


class CategoryRepository:
    def get_by_id(self, db: Session, category_id: str, shop_id: str) -> Category | None:
        return db.scalar(select(Category).where(Category.id == category_id, Category.shop_id == shop_id))

    def get_by_name(self, db: Session, name: str, shop_id: str) -> Category | None:
        normalized_name = name.strip().lower()
        return db.scalar(
            select(Category).where(
                Category.shop_id == shop_id,
                func.lower(func.trim(Category.name)) == normalized_name,
            )
        )

    def create(self, db: Session, payload: CategoryCreateSchema, shop_id: str) -> Category:
        category = Category(shop_id=shop_id, name=payload.name.strip())
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def update(self, db: Session, category: Category, payload: CategoryUpdateSchema) -> Category:
        category.name = payload.name.strip()
        db.commit()
        db.refresh(category)
        return category

    def delete(self, db: Session, category: Category) -> None:
        db.delete(category)
        db.commit()

    def list(self, db: Session, shop_id: str) -> list[Category]:
        stmt: Select[tuple[Category]] = select(Category).where(Category.shop_id == shop_id)
        stmt = stmt.order_by(Category.name.asc())
        return list(db.scalars(stmt).all())


category_repository = CategoryRepository()
