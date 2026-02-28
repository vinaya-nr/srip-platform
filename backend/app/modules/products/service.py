from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateException, NotFoundException, ValidationException
from app.modules.inventory.repository import inventory_repository
from app.modules.products.repository import product_repository
from app.modules.products.schemas import (
    ProductCreateSchema,
    ProductFilterSchema,
    ProductListResponseSchema,
    ProductResponseSchema,
    ProductStockResponseSchema,
    ProductUpdateSchema,
)


class ProductService:
    def create_product(self, db: Session, payload: ProductCreateSchema, shop_id: str) -> ProductResponseSchema:
        existing = product_repository.get_by_sku(db, payload.sku, shop_id)
        if existing:
            raise DuplicateException("SKU already exists in your shop.")
        if not payload.category_id:
            raise ValidationException("Category is required.")
        if not product_repository.category_exists(db, payload.category_id, shop_id):
            raise ValidationException("Category does not exist in your shop.")
        product = product_repository.create(db, payload, shop_id)
        return ProductResponseSchema.model_validate(product)

    def update_product(
        self,
        db: Session,
        product_id: str,
        payload: ProductUpdateSchema,
        shop_id: str,
    ) -> ProductResponseSchema:
        product = product_repository.get_by_id(db, product_id, shop_id)
        if not product:
            raise NotFoundException("No product found for provided ID.")

        if payload.sku:
            duplicate = product_repository.get_by_sku(db, payload.sku, shop_id)
            if duplicate and duplicate.id != product_id:
                raise DuplicateException("SKU already exists in your shop.")
        if "category_id" in payload.model_fields_set:
            if not payload.category_id:
                raise ValidationException("Category is required.")
            if not product_repository.category_exists(db, payload.category_id, shop_id):
                raise ValidationException("Category does not exist in your shop.")
        updated = product_repository.update(db, product, payload)
        return ProductResponseSchema.model_validate(updated)

    def get_product(self, db: Session, product_id: str, shop_id: str) -> ProductResponseSchema:
        product = product_repository.get_by_id(db, product_id, shop_id)
        if not product:
            raise NotFoundException("No product found for provided ID.")
        return ProductResponseSchema.model_validate(product)

    def list_products(
        self,
        db: Session,
        shop_id: str,
        filters: ProductFilterSchema,
        skip: int = 0,
        limit: int = 20,
    ) -> ProductListResponseSchema:
        products, total = product_repository.list(db, shop_id, filters, skip, limit)
        return ProductListResponseSchema(
            items=[ProductResponseSchema.model_validate(p) for p in products],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_product_stock(self, db: Session, product_id: str, shop_id: str) -> ProductStockResponseSchema:
        product = product_repository.get_by_id(db, product_id, shop_id)
        if not product:
            raise NotFoundException("No product found for provided ID.")
        return ProductStockResponseSchema(
            product_id=product_id,
            shop_id=shop_id,
            current_stock=inventory_repository.total_quantity(db, shop_id, product_id),
        )

    def delete_product(self, db: Session, product_id: str, shop_id: str) -> None:
        product = product_repository.get_by_id(db, product_id, shop_id)
        if not product:
            raise NotFoundException("No product found for provided ID.")
        product_repository.delete(db, product)


product_service = ProductService()
