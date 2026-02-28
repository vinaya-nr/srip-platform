from datetime import datetime

from pydantic import BaseModel, Field


class NotificationCreateSchema(BaseModel):
    event_type: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)


class NotificationResponseSchema(BaseModel):
    id: str
    shop_id: str
    event_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponseSchema(BaseModel):
    items: list[NotificationResponseSchema]
    total: int
    skip: int
    limit: int
