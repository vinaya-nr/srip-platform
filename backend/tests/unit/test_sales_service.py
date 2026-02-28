import pytest
from decimal import Decimal
from datetime import date, datetime

from app.core.exceptions import ValidationException
from app.modules.sales.service import sales_service
from app.modules.sales.schemas import SaleCreateSchema, SaleItemCreateSchema


class StubProduct:
    def __init__(self, id: str = "p1", price: float = 10.0, sku: str = "SKU-1", is_active: bool = True) -> None:
        self.id = id
        self.price = price
        self.sku = sku
        self.is_active = is_active


class StubSale:
    def __init__(self) -> None:
        self.id = "sale-1"
        self.shop_id = "s1"
        self.sale_number = "SN"
        self.total_amount = Decimal("10.00")
        self.created_at = datetime.utcnow()


class StubSaleItem:
    def __init__(self) -> None:
        self.id = "si-1"
        self.product_id = "p1"
        self.quantity = 1
        self.unit_price = Decimal("10.00")
        self.line_total = Decimal("10.00")


def test_create_sale_insufficient_stock(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr("app.modules.products.repository.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.repository.inventory_repository.total_quantity", lambda *_: 0)

    payload = SaleCreateSchema(items=[SaleItemCreateSchema(product_id="p1", quantity=1)])
    with pytest.raises(ValidationException):
        sales_service.create_sale(None, payload, "s1", "corr-1")


def test_create_sale_success(monkeypatch) -> None:  # noqa: ANN001
    class MockDB:
        def commit(self):
            pass
        def refresh(self, obj):
            pass

    monkeypatch.setattr("app.modules.products.repository.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.repository.inventory_repository.total_quantity", lambda *_: 5)
    monkeypatch.setattr("app.modules.sales.repository.sales_repository.create_sale", lambda *_args, **_kwargs: StubSale())
    monkeypatch.setattr("app.modules.sales.repository.sales_repository.add_sale_item", lambda *_args, **_kwargs: StubSaleItem())
    monkeypatch.setattr("app.modules.inventory.repository.inventory_repository.consume_stock", lambda *_: None)
    monkeypatch.setattr("app.modules.inventory.repository.inventory_repository.create_stock_movement", lambda *_args, **_kwargs: None)

    calls = []

    def fake_send_task(name, kwargs=None):
        calls.append((name, kwargs))

    monkeypatch.setattr("app.workers.celery_app.celery_app.send_task", fake_send_task)

    payload = SaleCreateSchema(items=[SaleItemCreateSchema(product_id="p1", quantity=1)])
    resp = sales_service.create_sale(MockDB(), payload, "s1", "corr-1")
    assert resp.total_amount == Decimal("10.00")
    assert len(calls) >= 1


def test_sales_repository_list_sales(monkeypatch) -> None:  # noqa: ANN001
    from app.modules.sales.repository import sales_repository

    sales_list = [StubSale(), StubSale()]

    class MockScalars:
        def all(self):
            return sales_list

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

        def scalar(self, stmt):
            return 2

    result, total = sales_repository.list_sales(MockDB(), "shop-1", 0, 20)
    assert len(result) == 2
    assert total == 2


def test_sales_repository_sale_items(monkeypatch) -> None:  # noqa: ANN001
    from app.modules.sales.repository import sales_repository

    items = [StubSaleItem(), StubSaleItem()]

    class MockScalars:
        def all(self):
            return items

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

    result = sales_repository.sale_items(MockDB(), "sale-1")
    assert len(result) == 2


def test_sales_repository_add_sale_item(monkeypatch) -> None:  # noqa: ANN001
    from app.modules.sales.repository import sales_repository

    class MockDB:
        def add(self, obj):
            pass

    item = sales_repository.add_sale_item(MockDB(), "s1", "p1", 2, 50.0, 100.0)
    assert item.sale_id == "s1"
    assert item.product_id == "p1"
    assert item.quantity == 2


def test_create_sale_product_not_active(monkeypatch) -> None:  # noqa: ANN001
    # product exists but is inactive
    monkeypatch.setattr("app.modules.products.repository.product_repository.get_by_id", lambda *_: StubProduct(is_active=False))
    payload = SaleCreateSchema(items=[SaleItemCreateSchema(product_id="p1", quantity=1)])
    with pytest.raises(ValidationException):
        sales_service.create_sale(None, payload, "s1", "corr-1")


def test_get_sale_not_found(monkeypatch) -> None:  # noqa: ANN001
    from app.core.exceptions import NotFoundException
    monkeypatch.setattr("app.modules.sales.repository.sales_repository.get_sale", lambda *_: None)
    with pytest.raises(NotFoundException):
        sales_service.get_sale(None, "s1", "nope")


def test_list_sales_service(monkeypatch) -> None:  # noqa: ANN001
    # ensure list_sales builds response schema
    from datetime import datetime
    class StubSaleBasic:
        def __init__(self):
            self.id = "s1"
            self.shop_id = "s1"
            self.sale_number = "n"
            self.total_amount = 10.0
            self.created_at = datetime.utcnow()
    monkeypatch.setattr(
        "app.modules.sales.repository.sales_repository.list_sales",
        lambda *_args, **_kwargs: ([StubSaleBasic()], 1),
    )
    monkeypatch.setattr(
        "app.modules.sales.repository.sales_repository.sale_items",
        lambda *_args, **_kwargs: [],
    )
    result = sales_service.list_sales(None, "s1")
    assert result.total == 1


def test_list_sales_service_passes_date_filters(monkeypatch) -> None:  # noqa: ANN001
    class StubSaleBasic:
        def __init__(self):
            self.id = "s1"
            self.shop_id = "s1"
            self.sale_number = "n"
            self.total_amount = 10.0
            self.created_at = datetime.utcnow()

    captured: dict[str, object] = {}

    def fake_list_sales(_db, _shop_id, _skip, _limit, from_date=None, to_date=None):
        captured["from_date"] = from_date
        captured["to_date"] = to_date
        return [StubSaleBasic()], 1

    monkeypatch.setattr("app.modules.sales.repository.sales_repository.list_sales", fake_list_sales)
    monkeypatch.setattr("app.modules.sales.repository.sales_repository.sale_items", lambda *_args, **_kwargs: [])

    result = sales_service.list_sales(None, "s1", from_date=date(2026, 2, 1), to_date=date(2026, 2, 28))
    assert result.total == 1
    assert captured["from_date"] == date(2026, 2, 1)
    assert captured["to_date"] == date(2026, 2, 28)


def test_list_sales_service_invalid_date_range_raises() -> None:
    with pytest.raises(ValidationException):
        sales_service.list_sales(None, "s1", from_date=date(2026, 3, 1), to_date=date(2026, 2, 1))



def test_sales_repository_create_sale(monkeypatch) -> None:  # noqa: ANN001
    from app.modules.sales.repository import sales_repository

    class MockDB:
        def add(self, obj):
            pass

        def flush(self):
            pass

    sale = sales_repository.create_sale(MockDB(), "shop-1", "SN-001", 100.0)
    assert sale.shop_id == "shop-1"
    assert sale.sale_number == "SN-001"
    assert sale.total_amount == 100.0
