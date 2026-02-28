from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreateSchema(BaseModel):
    category_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=180)
    sku: str = Field(min_length=1, max_length=80)
    description: str | None = None
    price: Decimal = Field(gt=0)
    low_stock_threshold: int = Field(default=5, ge=1)


class ProductUpdateSchema(BaseModel):
    category_id: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1, max_length=180)
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    low_stock_threshold: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class ProductFilterSchema(BaseModel):
    category_id: str | None = None
    search: str | None = None
    is_active: bool | None = True


class ProductResponseSchema(BaseModel):
    id: str
    shop_id: str
    category_id: str | None
    name: str
    sku: str
    description: str | None
    price: Decimal
    low_stock_threshold: int
    is_active: bool

    model_config = {"from_attributes": True}


class ProductListResponseSchema(BaseModel):
    items: list[ProductResponseSchema]
    total: int
    skip: int
    limit: int


class ProductStockResponseSchema(BaseModel):
    product_id: str
    shop_id: str
    current_stock: int
