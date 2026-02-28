from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateException, NotFoundException
from app.modules.categories.repository import category_repository
from app.modules.categories.schemas import CategoryCreateSchema, CategoryResponseSchema, CategoryUpdateSchema


class CategoryService:
    def create_category(self, db: Session, payload: CategoryCreateSchema, shop_id: str) -> CategoryResponseSchema:
        if category_repository.get_by_name(db, payload.name, shop_id):
            raise DuplicateException("Category already exists in your shop.")
        category = category_repository.create(db, payload, shop_id)
        return CategoryResponseSchema.model_validate(category)

    def list_categories(self, db: Session, shop_id: str) -> list[CategoryResponseSchema]:
        categories = category_repository.list(db, shop_id)
        return [CategoryResponseSchema.model_validate(category) for category in categories]

    def get_category(self, db: Session, category_id: str, shop_id: str) -> CategoryResponseSchema:
        category = category_repository.get_by_id(db, category_id, shop_id)
        if not category:
            raise NotFoundException("No category found for provided ID.")
        return CategoryResponseSchema.model_validate(category)

    def update_category(
        self,
        db: Session,
        category_id: str,
        payload: CategoryUpdateSchema,
        shop_id: str,
    ) -> CategoryResponseSchema:
        category = category_repository.get_by_id(db, category_id, shop_id)
        if not category:
            raise NotFoundException("No category found for provided ID.")

        duplicate = category_repository.get_by_name(db, payload.name, shop_id)
        if duplicate and duplicate.id != category_id:
            raise DuplicateException("Category already exists in your shop.")

        updated = category_repository.update(db, category, payload)
        return CategoryResponseSchema.model_validate(updated)

    def delete_category(self, db: Session, category_id: str, shop_id: str) -> None:
        category = category_repository.get_by_id(db, category_id, shop_id)
        if not category:
            raise NotFoundException("No category found for provided ID.")
        category_repository.delete(db, category)


category_service = CategoryService()
