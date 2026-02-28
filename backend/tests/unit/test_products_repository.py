import pytest
from decimal import Decimal

from app.modules.products.schemas import ProductCreateSchema, ProductFilterSchema, ProductUpdateSchema


class StubProduct:
    def __init__(self, product_id: str = "p1", sku: str = "SKU-1", name: str = "Prod", shop_id: str = "shop-1") -> None:
        self.id = product_id
        self.shop_id = shop_id
        self.category_id = None
        self.name = name
        self.sku = sku
        self.description = None
        self.price = Decimal("10.00")
        self.low_stock_threshold = 5
        self.is_active = True


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
