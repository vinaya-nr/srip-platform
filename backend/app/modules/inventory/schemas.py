from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class BatchCreateSchema(BaseModel):
    product_id: str
    quantity: int = Field(ge=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    expiry_date: date | None = None


class BatchResponseSchema(BaseModel):
    id: str
    shop_id: str
    product_id: str
    quantity: int
    unit_cost: Decimal | None
    expiry_date: date | None

    model_config = {"from_attributes": True}


class BatchListResponseSchema(BaseModel):
    items: list[BatchResponseSchema]
    total: int
    skip: int
    limit: int


class BatchMetadataUpdateSchema(BaseModel):
    unit_cost: Decimal | None = Field(default=None, ge=0)
    expiry_date: date | None = None


class StockMovementCreateSchema(BaseModel):
    product_id: str
    batch_id: str
    movement_type: Literal["in", "out", "adjustment"]
    quantity: int = Field(gt=0)
    adjustment_mode: Literal["increase", "decrease"] | None = None
    unit_cost: Decimal | None = Field(default=None, ge=0)
    expiry_date: date | None = None
    reason: str | None = None


class StockMovementResponseSchema(BaseModel):
    id: str
    shop_id: str
    product_id: str
    movement_type: str
    quantity: int
    reason: str | None

    model_config = {"from_attributes": True}
