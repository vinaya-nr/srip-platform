import pytest
from decimal import Decimal

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.inventory.schemas import StockMovementCreateSchema, BatchCreateSchema, BatchMetadataUpdateSchema
from app.modules.inventory.service import inventory_service


class StubProduct:
    def __init__(self) -> None:
        self.id = "product-1"
        self.shop_id = "shop-1"
        self.sku = "SKU-1"
        self.is_active = True
        self.name = "Product"
        self.category_id = None
        self.description = None
        self.price = 10
        self.low_stock_threshold = 5


class StubBatch:
    def __init__(self, id: str = "b1", shop_id: str = "shop-1", product_id: str = "p1", quantity: int = 5, expiry_date: str | None = None) -> None:
        self.id = id
        self.shop_id = shop_id
        self.product_id = product_id
        self.quantity = quantity
        self.unit_cost = Decimal("1.00")
        self.expiry_date = expiry_date


class StubMovement:
    def __init__(self, id: str = "m1", shop_id: str = "s1", product_id: str = "p1"):
        self.id = id
        self.shop_id = shop_id
        self.product_id = product_id
        self.movement_type = "in"
        self.quantity = 5
        self.reason = None


def test_record_movement_product_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: None)
    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="out", quantity=1)
    with pytest.raises(ValidationException):
        inventory_service.record_movement(None, payload, "shop-1", "corr-1")  # type: ignore[arg-type]

def test_create_batch_product_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.products.repository.product_repository.get_by_id", lambda *_: None)
    payload = BatchCreateSchema(product_id="p1", quantity=5)
    with pytest.raises(ValidationException):
        inventory_service.create_batch(None, payload, "shop-1")  # type: ignore[arg‑type]


def test_record_movement_in_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    # covers the "in" movement branch
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=5))
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.create_stock_movement", lambda *_args, **_kwargs: StubMovement())
    class MockDB:
        def commit(self):
            pass
        def refresh(self, obj):
            pass
    calls = []
    def fake_send_task(name, kwargs=None):
        calls.append(name)
    monkeypatch.setattr("app.workers.celery_app.celery_app.send_task", fake_send_task)
    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="in", quantity=3)
    res = inventory_service.record_movement(MockDB(), payload, "shop-1", "corr")
    assert res.product_id == "p1"
    assert calls, "tasks should have been sent"


def test_record_movement_adjustment_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    # increase adjustment
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=5))
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.create_stock_movement", lambda *_args, **_kwargs: StubMovement())
    monkeypatch.setattr("app.modules.inventory.service.celery_app.send_task", lambda *_args, **_kwargs: None)
    class MockDB2:
        def commit(self):
            pass
        def refresh(self, obj):
            pass
    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="adjustment", quantity=2, adjustment_mode="increase")
    inventory_service.record_movement(MockDB2(), payload, "shop-1", "corr")  # should not raise

    # decrease adjustment insufficient
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=0))
    payload2 = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="adjustment", quantity=5, adjustment_mode="decrease")
    with pytest.raises(ValidationException):
        inventory_service.record_movement(None, payload2, "shop-1", "corr")

def test_record_movement_out_insufficient(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=0))
    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="out", quantity=2)
    with pytest.raises(ValidationException):
        inventory_service.record_movement(None, payload, "shop-1", "corr-1")  # type: ignore[arg-type]


def test_record_adjustment_requires_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=5))
    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="adjustment", quantity=1)
    with pytest.raises(ValidationException):
        inventory_service.record_movement(None, payload, "shop-1", "corr-1")  # type: ignore[arg-type]


def test_create_batch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.products.repository.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.repository.inventory_repository.create_batch", lambda *_args, **_kwargs: StubBatch())

    payload = BatchCreateSchema(product_id="p1", quantity=5)
    res = inventory_service.create_batch(None, payload, "shop-1")
    assert res.product_id == "p1"


def test_update_batch_metadata_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: None)
    with pytest.raises(NotFoundException):
        inventory_service.update_batch_metadata(
            None,  # type: ignore[arg-type]
            "b1",
            BatchMetadataUpdateSchema(unit_cost=Decimal("5.00"), expiry_date="2031-01-01"),
            "shop-1",
        )


def test_update_batch_metadata_success(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_batch = StubBatch(id="b1", quantity=9)
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: stub_batch)
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.update_batch_metadata", lambda *_args, **_kwargs: stub_batch)

    result = inventory_service.update_batch_metadata(
        None,  # type: ignore[arg-type]
        "b1",
        BatchMetadataUpdateSchema(unit_cost=Decimal("8.00"), expiry_date="2031-02-01"),
        "shop-1",
    )
    assert result.id == "b1"


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


def test_create_batch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful batch creation."""
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.create_batch", lambda *_args, **_kwargs: StubBatch())
    
    payload = BatchCreateSchema(product_id="p1", quantity=100)
    result = inventory_service.create_batch(None, payload, "shop-1")  # type: ignore[arg-type]
    assert result.id == "b1"


def test_create_batch_product_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test batch creation when product doesn't exist."""
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: None)
    
    payload = BatchCreateSchema(product_id="missing", quantity=50)
    with pytest.raises(ValidationException):
        inventory_service.create_batch(None, payload, "shop-1")  # type: ignore[arg-type]


def test_list_batches_with_all_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test listing all batches."""
    batches = [StubBatch(id="b1"), StubBatch(id="b2"), StubBatch(id="b3")]
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.list_batches", lambda *_: (batches, 3))
    
    result = inventory_service.list_batches(None, "shop-1")  # type: ignore[arg-type]
    assert len(result.items) == 3


def test_list_batches_with_product_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test listing batches filtered by product."""
    batches = [StubBatch(product_id="p1")]
    
    def mock_list(*args):
        assert args[2] == "p1"
        return batches, 1
    
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.list_batches", mock_list)
    
    result = inventory_service.list_batches(None, "shop-1", product_id="p1")  # type: ignore[arg-type]
    assert len(result.items) == 1


def test_record_movement_stock_in_with_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test stock-in movement with expiry date."""
    class MockDB:
        def commit(self):
            pass
        def refresh(self, obj):
            pass

    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=5))
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.create_stock_movement", lambda *_args, **_kwargs: StubMovement())
    monkeypatch.setattr("app.modules.inventory.service.celery_app.send_task", lambda *_args, **_kwargs: None)
    
    payload = StockMovementCreateSchema(
        product_id="p1", 
        batch_id="b1",
        movement_type="in", 
        quantity=50,
        unit_cost=Decimal("10.00"),
        expiry_date="2026-12-31"
    )
    result = inventory_service.record_movement(MockDB(), payload, "shop-1", "corr-123")  # type: ignore[arg-type]
    assert result.id == "m1"


def test_record_movement_batch_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: None)

    payload = StockMovementCreateSchema(product_id="p1", batch_id="missing", movement_type="out", quantity=1)
    with pytest.raises(NotFoundException):
        inventory_service.record_movement(None, payload, "shop-1", "corr-123")  # type: ignore[arg-type]


def test_record_movement_batch_product_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr(
        "app.modules.inventory.service.inventory_repository.get_batch",
        lambda *_args, **_kwargs: StubBatch(product_id="another-product", quantity=10),
    )

    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="out", quantity=1)
    with pytest.raises(ValidationException):
        inventory_service.record_movement(None, payload, "shop-1", "corr-123")  # type: ignore[arg-type]


def test_record_movement_adjustment_mode_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that adjustment mode is required for adjustment movements."""
    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=5))
    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="adjustment", quantity=10)
    with pytest.raises(ValidationException):
        inventory_service.record_movement(None, payload, "shop-1", "corr-123")  # type: ignore[arg-type]


def test_get_expiry_alerts_within_days(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting expiry alerts with custom day threshold."""
    batches = [StubBatch(id="exp-1", expiry_date="2026-03-15")]
    
    def mock_expiring(*args):
        assert args[2] == 15  # Verify within_days parameter
        return batches
    
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.expiring_batches", mock_expiring)
    
    result = inventory_service.get_expiry_alerts(None, "shop-1", within_days=15)  # type: ignore[arg-type]
    assert len(result) == 1


def test_record_movement_with_unit_cost_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test stock-in movement without unit cost."""
    class MockDB:
        def commit(self):
            pass
        def refresh(self, obj):
            pass

    monkeypatch.setattr("app.modules.inventory.service.product_repository.get_by_id", lambda *_: StubProduct())
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.get_batch", lambda *_args, **_kwargs: StubBatch(quantity=5))
    monkeypatch.setattr("app.modules.inventory.service.inventory_repository.create_stock_movement", lambda *_args, **_kwargs: StubMovement())
    monkeypatch.setattr("app.modules.inventory.service.celery_app.send_task", lambda *_args, **_kwargs: None)
    
    payload = StockMovementCreateSchema(product_id="p1", batch_id="b1", movement_type="in", quantity=50, unit_cost=None)
    result = inventory_service.record_movement(MockDB(), payload, "shop-1", "corr-123")  # type: ignore[arg-type]
    assert result.id == "m1"
