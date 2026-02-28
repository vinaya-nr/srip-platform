from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.users.models import Shop, User


class UserRepository:
    def get_user_by_id(self, db: Session, user_id: str, shop_id: str | None = None) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if shop_id:
            stmt = stmt.where(User.shop_id == shop_id)
        return db.scalar(stmt)

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email.lower()))

    def get_shop_by_id(self, db: Session, shop_id: str) -> Shop | None:
        return db.scalar(select(Shop).where(Shop.id == shop_id))

    def get_shop_by_name(self, db: Session, name: str) -> Shop | None:
        normalized_name = name.strip().lower()
        return db.scalar(select(Shop).where(func.lower(func.trim(Shop.name)) == normalized_name))

    def create_shop(self, db: Session, name: str) -> Shop:
        shop = Shop(name=name.strip())
        db.add(shop)
        db.flush()
        return shop

    def create_user(self, db: Session, shop_id: str, email: str, password_hash: str) -> User:
        user = User(shop_id=shop_id, email=email.lower(), password_hash=password_hash, is_active=True)
        db.add(user)
        db.flush()
        return user


user_repository = UserRepository()
