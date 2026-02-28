import pytest

from app.core.exceptions import DuplicateException, NotFoundException
from app.modules.users.service import user_service
from app.modules.users.schemas import UserCreateSchema


class StubUser:
    def __init__(self, id: str = "u1", email: str = "u@ex.com", is_active: bool = True):
        from datetime import datetime
        
        self.id = id
        self.email = email
        self.is_active = is_active
        self.shop_id = "shop-1"
        self.created_at = datetime.utcnow()


class StubShop:
    def __init__(self, id: str = "s1", name: str = "Shop"):
        from datetime import datetime
        
        self.id = id
        self.name = name
        self.created_at = datetime.utcnow()


def test_create_user_duplicate_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_email", lambda *_: StubUser())

    with pytest.raises(DuplicateException):
        user_service.create_user(None, UserCreateSchema(email="u@ex.com", password="password123", shop_name="Shop"))


def test_create_user_duplicate_shop_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_email", lambda *_: None)
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_shop_by_name", lambda *_: StubShop())

    with pytest.raises(DuplicateException):
        user_service.create_user(None, UserCreateSchema(email="u@ex.com", password="password123", shop_name="Shop"))


def test_create_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDB:
        def commit(self):
            pass

        def refresh(self, obj):
            pass

    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_email", lambda *_: None)
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_shop_by_name", lambda *_: None)
    monkeypatch.setattr("app.modules.users.repository.user_repository.create_shop", lambda *_: StubShop())
    monkeypatch.setattr("app.modules.users.repository.user_repository.create_user", lambda *_args, **_kwargs: StubUser())
    monkeypatch.setattr("app.core.security.hash_password", lambda *_: "hashed")

    res = user_service.create_user(MockDB(), UserCreateSchema(email="u@ex.com", password="password123", shop_name="Shop"))
    assert res.email == "u@ex.com"


def test_get_profile_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_id", lambda *_: None)

    with pytest.raises(NotFoundException):
        user_service.get_profile(None, "u1", "s1")


def test_get_profile_shop_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_id", lambda *_: StubUser())
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_shop_by_id", lambda *_: None)

    with pytest.raises(NotFoundException):
        user_service.get_profile(None, "u1", "s1")


def test_get_profile_success(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_user = StubUser()
    stub_shop = StubShop()
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_id", lambda *_: stub_user)
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_shop_by_id", lambda *_: stub_shop)

    res = user_service.get_profile(None, "u1", "s1")
    assert res.user.email == "u@ex.com"
    assert res.shop.name == "Shop"
