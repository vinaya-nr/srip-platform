import pytest
from decimal import Decimal

from app.core.exceptions import DuplicateException, NotFoundException, ValidationException
from app.modules.products.schemas import ProductCreateSchema, ProductFilterSchema, ProductUpdateSchema
from app.modules.products.service import product_service


class StubProduct:
    def __init__(self, product_id: str = "p1", sku: str = "S1", name: str = "Prod", shop_id: str = "shop-1") -> None:
        self.id = product_id
        self.shop_id = shop_id
        self.category_id = None
        self.name = name
        self.sku = sku
        self.description = None
        self.price = Decimal("10.00")
        self.low_stock_threshold = 5
        self.is_active = True


def test_create_product_duplicate_sku(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_sku", lambda *_: StubProduct(product_id="p1"))
    payload = ProductCreateSchema(name="A", sku="S1", price=10, category_id="cat-1")
    with pytest.raises(DuplicateException):
        product_service.create_product(None, payload, "shop-1")  # type: ignore[arg-type]


def test_create_product_missing_category(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_sku", lambda *_: None)
    monkeypatch.setattr("app.modules.products.service.product_repository.category_exists", lambda *_: False)
    payload = ProductCreateSchema(name="A", sku="S1", price=10, category_id="cat-1")
    with pytest.raises(ValidationException):
        product_service.create_product(None, payload, "shop-1")  # type: ignore[arg-type]


def test_create_product_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.products.repository.product_repository.get_by_sku", lambda *_: None)
    monkeypatch.setattr("app.modules.products.repository.product_repository.category_exists", lambda *_: True)
    monkeypatch.setattr("app.modules.products.repository.product_repository.create", lambda *_args, **_kwargs: StubProduct())

    payload = ProductCreateSchema(name="A", sku="S1", price=Decimal("10.00"), category_id="cat-1")
    res = product_service.create_product(None, payload, "shop-1")
    assert res.sku == "S1"


def test_update_product_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: None)
    with pytest.raises(NotFoundException):
        product_service.update_product(None, "missing", ProductUpdateSchema(name="X"), "shop-1")  # type: ignore[arg-type]


def test_list_products_returns_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.products.service.product_repository.list",
        lambda *_: ([StubProduct(product_id="p1"), StubProduct(product_id="p2", sku="SKU-2")], 2),
    )
    result = product_service.list_products(None, "shop-1", ProductFilterSchema())  # type: ignore[arg-type]
    assert len(result.items) == 2


def test_products_repository_get_by_sku(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.products.repository import product_repository

    class MockDB:
        def scalar(self, stmt):
            return StubProduct(sku="S1")

    result = product_repository.get_by_sku(MockDB(), "S1", "shop-1")
    assert result.sku == "S1"


def test_products_repository_get_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.products.repository import product_repository

    class MockDB:
        def scalar(self, stmt):
            return StubProduct()

    result = product_repository.get_by_id(MockDB(), "p1", "shop-1")
    assert result.id == "p1"


def test_products_repository_list(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.products.repository import product_repository

    products = [StubProduct(product_id="p1"), StubProduct(product_id="p2")]

    class MockScalars:
        def all(self):
            return products

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

        def scalar(self, stmt):
            return 2

    result, total = product_repository.list(MockDB(), "shop-1", ProductFilterSchema(), 0, 20)
    assert len(result) == 2
    assert total == 2


def test_products_repository_category_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.products.repository import product_repository

    class MockDB:
        def scalar(self, stmt):
            return True

    result = product_repository.category_exists(MockDB(), "cat-1", "shop-1")
    assert result is True


def test_products_repository_create(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.products.repository import product_repository

    class MockDB:
        def add(self, obj):
            pass

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    payload = ProductCreateSchema(name="Test", sku="T1", price=Decimal("10.00"), category_id="cat-1")
    product = product_repository.create(MockDB(), payload, "shop-1")
    assert product.name == "Test"


def test_products_repository_update(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.products.repository import product_repository

    class MockDB:
        def commit(self):
            pass

        def refresh(self, obj):
            pass

    stub_product = StubProduct()
    payload = ProductUpdateSchema(name="Updated")
    product_repository.update(MockDB(), stub_product, payload)
    assert stub_product.name == "Updated"

def test_update_product_duplicate_sku(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test updating product with duplicate SKU."""
    existing_product = StubProduct(product_id="p2", sku="S2")
    
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: StubProduct(product_id="p1"))
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_sku", lambda *_: existing_product)
    
    payload = ProductUpdateSchema(name="Updated", sku="S2")
    with pytest.raises(DuplicateException):
        product_service.update_product(None, "p1", payload, "shop-1")  # type: ignore[arg-type]


def test_update_product_missing_category(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test updating product with missing category."""
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: StubProduct(product_id="p1"))
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_sku", lambda *_: None)
    monkeypatch.setattr("app.modules.products.service.product_repository.category_exists", lambda *_: False)
    
    payload = ProductUpdateSchema(name="Updated", category_id="cat-1")
    with pytest.raises(ValidationException):
        product_service.update_product(None, "p1", payload, "shop-1")  # type: ignore[arg-type]


def test_update_product_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful product update."""
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: StubProduct(product_id="p1"))
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_sku", lambda *_: None)
    monkeypatch.setattr("app.modules.products.service.product_repository.update", lambda *_args, **_kwargs: StubProduct(product_id="p1", name="Updated"))
    
    payload = ProductUpdateSchema(name="Updated")
    result = product_service.update_product(None, "p1", payload, "shop-1")  # type: ignore[arg-type]
    assert result.name == "Updated"


def test_get_product_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful product retrieval."""
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: StubProduct())
    
    result = product_service.get_product(None, "p1", "shop-1")  # type: ignore[arg-type]
    assert result.id == "p1"


def test_get_product_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting non-existent product."""
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: None)
    
    with pytest.raises(NotFoundException):
        product_service.get_product(None, "missing", "shop-1")  # type: ignore[arg-type]


def test_delete_product_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test deleting non-existent product."""
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: None)
    
    with pytest.raises(NotFoundException):
        product_service.delete_product(None, "missing", "shop-1")  # type: ignore[arg-type]


def test_delete_product_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful product deletion."""
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.products.service.product_repository.delete", lambda *_args, **_kwargs: None)
    
    product_service.delete_product(None, "p1", "shop-1")  # type: ignore[arg-type]


def test_update_product_same_sku(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test updating product with same SKU (should succeed)."""
    product = StubProduct(product_id="p1", sku="S1")
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_id", lambda *_: product)
    monkeypatch.setattr("app.modules.products.service.product_repository.get_by_sku", lambda *_: product)
    monkeypatch.setattr("app.modules.products.service.product_repository.update", lambda *_args, **_kwargs: product)
    
    payload = ProductUpdateSchema(name="Updated", sku="S1")
    result = product_service.update_product(None, "p1", payload, "shop-1")  # type: ignore[arg-type]
    assert result.id == "p1"
