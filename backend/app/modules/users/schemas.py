from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    shop_name: str = Field(min_length=1, max_length=200)


class UserResponseSchema(BaseModel):
    id: str
    shop_id: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ShopResponseSchema(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileSchema(BaseModel):
    user: UserResponseSchema
    shop: ShopResponseSchema
