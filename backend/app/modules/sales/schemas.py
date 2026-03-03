from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SaleItemCreateSchema(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class SaleCreateSchema(BaseModel):
    items: list[SaleItemCreateSchema] = Field(min_length=1)


class SaleItemResponseSchema(BaseModel):
    product_id: str
    product_name: str | None = None
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class SaleResponseSchema(BaseModel):
    id: str
    shop_id: str
    sale_number: str
    total_amount: Decimal
    created_at: datetime
    items: list[SaleItemResponseSchema]


class SaleListResponseSchema(BaseModel):
    items: list[SaleResponseSchema]
    total: int
    skip: int
    limit: int
