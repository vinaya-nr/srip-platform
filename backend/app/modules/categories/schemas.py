from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class CategoryUpdateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class CategoryResponseSchema(BaseModel):
    id: str
    shop_id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
