import pytest
from decimal import Decimal
from datetime import date


class StubBatch:
    def __init__(self, id: str = "b1", shop_id: str = "s1", product_id: str = "p1", quantity: int = 5):
        self.id = id
        self.shop_id = shop_id
        self.product_id = product_id
        self.quantity = quantity
        self.unit_cost = Decimal("1.00")
        self.expiry_date = None


class StubMovement:
    def __init__(self, id: str = "m1", shop_id: str = "s1", product_id: str = "p1"):
        self.id = id
        self.shop_id = shop_id
        self.product_id = product_id
        self.movement_type = "in"
        self.quantity = 5
        self.reason = None


def test_inventory_repository_create_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.inventory.repository import inventory_repository
    from app.modules.inventory.schemas import BatchCreateSchema

    class MockDB:
        def add(self, obj):
            pass

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    payload = BatchCreateSchema(product_id="p1", quantity=5)
    batch = inventory_repository.create_batch(MockDB(), payload, "s1")
    assert batch.product_id == "p1"


def test_inventory_repository_list_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.inventory.repository import inventory_repository

    batches = [StubBatch(id="b1"), StubBatch(id="b2")]

    class MockScalars:
        def all(self):
            return batches

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

        def scalar(self, stmt):
            return 2

    result, total = inventory_repository.list_batches(MockDB(), "s1")
    assert len(result) == 2
    assert total == 2


def test_inventory_repository_list_batches_by_product(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.inventory.repository import inventory_repository

    batches = [StubBatch(product_id="p1")]

    class MockScalars:
        def all(self):
            return batches

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

        def scalar(self, stmt):
            return 1

    result, total = inventory_repository.list_batches(MockDB(), "s1", product_id="p1")
    assert len(result) == 1
    assert total == 1


def test_inventory_repository_total_quantity(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.inventory.repository import inventory_repository

    class MockScalars:
        def all(self):
            return [StubBatch(quantity=10)]

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

    result = inventory_repository.total_quantity(MockDB(), "s1", "p1")
    assert result == 10


def test_inventory_repository_create_stock_movement(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.inventory.repository import inventory_repository
    from app.modules.inventory.schemas import StockMovementCreateSchema

    class MockDB:
        def add(self, obj):
            pass

        def flush(self):
            pass

    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="in", quantity=5)
    movement = inventory_repository.create_stock_movement(MockDB(), payload, "s1", autocommit=False)
    assert movement.product_id == "p1"


def test_inventory_repository_consume_stock(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.inventory.repository import inventory_repository

    class MockScalars:
        def all(self):
            return [StubBatch(quantity=5)]

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

        def execute(self, stmt):
            pass

    db = MockDB()
    inventory_repository.consume_stock(db, "s1", "p1", 2)


def test_inventory_repository_increase_stock(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.inventory.repository import inventory_repository

    class MockDB:
        def add(self, obj):
            pass

        def flush(self):
            pass

    inventory_repository.increase_stock(MockDB(), "s1", "p1", 5, unit_cost=Decimal("1.00"))
