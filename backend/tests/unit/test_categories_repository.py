import pytest

from app.modules.categories.schemas import CategoryCreateSchema, CategoryUpdateSchema


class StubCategory:
    def __init__(self, id: str = "cat-1", shop_id: str = "shop-1", name: str = "Groceries") -> None:
        self.id = id
        self.shop_id = shop_id
        self.name = name


def test_categories_repository_get_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.categories.repository import category_repository

    class MockDB:
        def scalar(self, _stmt):
            return StubCategory()

    result = category_repository.get_by_id(MockDB(), "cat-1", "shop-1")
    assert result.id == "cat-1"


def test_categories_repository_get_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.categories.repository import category_repository

    class MockDB:
        def scalar(self, _stmt):
            return StubCategory(name="Groceries")

    result = category_repository.get_by_name(MockDB(), " groceries ", "shop-1")
    assert result.name == "Groceries"


def test_categories_repository_create(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.categories.repository import category_repository

    class MockDB:
        def add(self, _obj):
            pass

        def commit(self):
            pass

        def refresh(self, _obj):
            pass

    category = category_repository.create(MockDB(), CategoryCreateSchema(name=" Groceries "), "shop-1")
    assert category.name == "Groceries"


def test_categories_repository_update(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.categories.repository import category_repository

    class MockDB:
        def commit(self):
            pass

        def refresh(self, _obj):
            pass

    category = StubCategory(name="Old")
    updated = category_repository.update(MockDB(), category, CategoryUpdateSchema(name=" New "))
    assert updated.name == "New"


def test_categories_repository_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.categories.repository import category_repository

    deleted = {"called": False}

    class MockDB:
        def delete(self, _obj):
            deleted["called"] = True

        def commit(self):
            pass

    category_repository.delete(MockDB(), StubCategory())
    assert deleted["called"] is True


def test_categories_repository_list(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.categories.repository import category_repository

    class MockScalars:
        def all(self):
            return [StubCategory(), StubCategory(id="cat-2", name="Snacks")]

    class MockDB:
        def scalars(self, _stmt):
            return MockScalars()

    result = category_repository.list(MockDB(), "shop-1")
    assert len(result) == 2
