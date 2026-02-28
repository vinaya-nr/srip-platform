from datetime import datetime

import pytest

from app.core.exceptions import DuplicateException, NotFoundException
from app.modules.categories.schemas import CategoryCreateSchema, CategoryUpdateSchema
from app.modules.categories.service import category_service


class StubCategory:
    def __init__(self, id: str = "cat-1", shop_id: str = "shop-1", name: str = "Groceries") -> None:
        self.id = id
        self.shop_id = shop_id
        self.name = name
        self.created_at = datetime.now()


def test_create_category_duplicate_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_name", lambda *_: StubCategory())

    with pytest.raises(DuplicateException):
        category_service.create_category(None, CategoryCreateSchema(name="Groceries"), "shop-1")


def test_create_category_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_name", lambda *_: None)
    monkeypatch.setattr("app.modules.categories.repository.category_repository.create", lambda *_: StubCategory())

    result = category_service.create_category(None, CategoryCreateSchema(name="Groceries"), "shop-1")
    assert result.name == "Groceries"


def test_get_category_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_id", lambda *_: None)

    with pytest.raises(NotFoundException):
        category_service.get_category(None, "missing", "shop-1")


def test_get_category_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_id", lambda *_: StubCategory())

    result = category_service.get_category(None, "cat-1", "shop-1")
    assert result.id == "cat-1"


def test_update_category_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_id", lambda *_: None)

    with pytest.raises(NotFoundException):
        category_service.update_category(None, "missing", CategoryUpdateSchema(name="Snacks"), "shop-1")


def test_update_category_duplicate_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_id", lambda *_: StubCategory(id="cat-1"))
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_name", lambda *_: StubCategory(id="cat-2"))

    with pytest.raises(DuplicateException):
        category_service.update_category(None, "cat-1", CategoryUpdateSchema(name="Snacks"), "shop-1")


def test_update_category_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_id", lambda *_: StubCategory(id="cat-1"))
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_name", lambda *_: None)
    monkeypatch.setattr(
        "app.modules.categories.repository.category_repository.update",
        lambda *_: StubCategory(id="cat-1", name="Snacks"),
    )

    result = category_service.update_category(None, "cat-1", CategoryUpdateSchema(name="Snacks"), "shop-1")
    assert result.name == "Snacks"


def test_delete_category_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_id", lambda *_: None)

    with pytest.raises(NotFoundException):
        category_service.delete_category(None, "missing", "shop-1")


def test_delete_category_success(monkeypatch: pytest.MonkeyPatch) -> None:
    deleted = {"called": False}

    def _delete(*_args, **_kwargs) -> None:
        deleted["called"] = True

    monkeypatch.setattr("app.modules.categories.repository.category_repository.get_by_id", lambda *_: StubCategory())
    monkeypatch.setattr("app.modules.categories.repository.category_repository.delete", _delete)

    category_service.delete_category(None, "cat-1", "shop-1")
    assert deleted["called"] is True


def test_list_categories_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.categories.repository.category_repository.list",
        lambda *_: [StubCategory(id="cat-1"), StubCategory(id="cat-2", name="Snacks")],
    )

    result = category_service.list_categories(None, "shop-1")
    assert len(result) == 2
