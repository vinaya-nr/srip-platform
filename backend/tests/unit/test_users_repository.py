import pytest

from app.modules.users.schemas import UserCreateSchema


class StubUser:
    def __init__(self, id: str = "u1", email: str = "u@ex.com", is_active: bool = True):
        from datetime import datetime
        
        self.id = id
        self.email = email
        self.is_active = is_active
        self.shop_id = "s1"
        self.created_at = datetime.utcnow()


class StubShop:
    def __init__(self, id: str = "s1", name: str = "Shop"):
        from datetime import datetime
        
        self.id = id
        self.name = name
        self.created_at = datetime.utcnow()


def test_users_repository_get_user_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.users.repository import user_repository

    class MockDB:
        def scalar(self, stmt):
            return StubUser()

    result = user_repository.get_user_by_id(MockDB(), "u1")
    assert result.id == "u1"


def test_users_repository_get_user_by_id_with_shop(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.users.repository import user_repository

    class MockDB:
        def scalar(self, stmt):
            return StubUser()

    result = user_repository.get_user_by_id(MockDB(), "u1", "s1")
    assert result.shop_id == "s1"


def test_users_repository_get_user_by_email(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.users.repository import user_repository

    class MockDB:
        def scalar(self, stmt):
            return StubUser(email="test@example.com")

    result = user_repository.get_user_by_email(MockDB(), "test@example.com")
    assert result.email == "test@example.com"


def test_users_repository_get_shop_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.users.repository import user_repository

    class MockDB:
        def scalar(self, stmt):
            return StubShop()

    result = user_repository.get_shop_by_id(MockDB(), "s1")
    assert result.id == "s1"


def test_users_repository_get_shop_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.users.repository import user_repository

    class MockDB:
        def scalar(self, stmt):
            return StubShop(name="My Shop")

    result = user_repository.get_shop_by_name(MockDB(), "  my shop  ")
    assert result.name == "My Shop"


def test_users_repository_create_shop(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.users.repository import user_repository

    class MockDB:
        def add(self, obj):
            pass

        def flush(self):
            pass

    shop = user_repository.create_shop(MockDB(), "  My Shop  ")
    assert shop.name == "My Shop"


def test_users_repository_create_user(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.users.repository import user_repository

    class MockDB:
        def add(self, obj):
            pass

        def flush(self):
            pass

    user = user_repository.create_user(MockDB(), "s1", "user@example.com", "hashed_pwd")
    assert user.shop_id == "s1"
    assert user.email == "user@example.com"
    assert user.is_active is True
