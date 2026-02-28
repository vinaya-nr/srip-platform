from pydantic import BaseModel, EmailStr


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class CurrentUserSchema(BaseModel):
    id: str
    email: EmailStr
    shop_id: str


class TokenPayload(BaseModel):
    sub: str
    shop_id: str | None = None
    jti: str
    exp: int
    iat: int
    token_type: str


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: CurrentUserSchema

