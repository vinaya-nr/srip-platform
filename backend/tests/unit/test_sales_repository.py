import pytest
from decimal import Decimal
from datetime import datetime


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
