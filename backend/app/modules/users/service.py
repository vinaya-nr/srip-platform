from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateException, NotFoundException
from app.core.security import hash_password
from app.modules.users.repository import user_repository
from app.modules.users.schemas import ShopResponseSchema, UserCreateSchema, UserProfileSchema, UserResponseSchema


class UserService:
    def create_user(self, db: Session, payload: UserCreateSchema) -> UserResponseSchema:
        if user_repository.get_user_by_email(db, payload.email):
            raise DuplicateException("Email already registered.")
        if user_repository.get_shop_by_name(db, payload.shop_name):
            raise DuplicateException("Shop name already registered.")

        shop = user_repository.create_shop(db, payload.shop_name)
        user = user_repository.create_user(db, shop.id, payload.email, hash_password(payload.password))
        db.commit()
        db.refresh(user)
        return UserResponseSchema.model_validate(user)

    def get_profile(self, db: Session, user_id: str, shop_id: str) -> UserProfileSchema:
        user = user_repository.get_user_by_id(db, user_id, shop_id)
        if not user:
            raise NotFoundException("User not found.")
        shop = user_repository.get_shop_by_id(db, shop_id)
        if not shop:
            raise NotFoundException("Shop not found.")
        return UserProfileSchema(
            user=UserResponseSchema.model_validate(user),
            shop=ShopResponseSchema.model_validate(shop),
        )


user_service = UserService()
