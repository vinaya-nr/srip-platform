"""Comprehensive tests for analytics worker tasks."""

import pytest
from datetime import date
from unittest.mock import Mock
from app.workers.tasks.analytics import (
    ingest_sale_event,
    stream_inventory_event,
    compute_slow_movers,
    nightly_snapshot
)


def test_ingest_sale_event_with_items(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test sale event ingestion with items."""
    sale_row = {
        "id": "sale-1",
        "shop_id": "shop-1",
        "sale_number": "SAL-001",
        "total_amount": 500.0,
        "created_at": "2026-02-20",
    }
    items = [
        {
            "product_id": "prod-1",
            "quantity": 5,
            "unit_price": 100.0,
            "line_total": 500.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=sale_row)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=items)
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-0")
    
    result = ingest_sale_event("sale-1", "shop-1", "corr-123")
    
    assert result["event_type"] == "sale_ingested"
    assert result["sale_id"] == "sale-1"
    assert result["shop_id"] == "shop-1"
    assert result["total_amount"] == 500.0


def test_ingest_sale_event_no_sale_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test sale ingestion when sale is not found."""
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=None)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=[])
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-1")
    
    result = ingest_sale_event("missing", "shop-1", "corr-123")
    
    assert result["sale_number"] == ""
    assert result["total_amount"] == 0.0
    assert result["items"] == []


def test_stream_inventory_event_addition(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test inventory event streaming for stock addition."""
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "2-0")
    
    result = stream_inventory_event(
        shop_id="shop-1",
        product_id="prod-1",
        movement_type="addition",
        quantity=100,
        correlation_id="corr-123"
    )
    
    assert result["event_type"] == "inventory_stream"
    assert result["movement_type"] == "addition"
    assert result["quantity"] == 100


def test_stream_inventory_event_removal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test inventory event streaming for stock removal."""
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "2-1")
    
    result = stream_inventory_event(
        shop_id="shop-1",
        product_id="prod-1",
        movement_type="removal",
        quantity=50,
        correlation_id="corr-456"
    )
    
    assert result["movement_type"] == "removal"
    assert result["quantity"] == 50


def test_compute_slow_movers_multiple_products(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test slow movers computation with multiple products."""
    slow_movers = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Slow Product 1",
            "sold_qty": 2,
        },
        {
            "shop_id": "shop-1",
            "product_id": "prod-2",
            "name": "Slow Product 2",
            "sold_qty": 3,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=slow_movers)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = compute_slow_movers()
    
    assert result == 2


def test_compute_slow_movers_with_shop_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test slow movers computation filtered by shop."""
    slow_movers = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Slow Product",
            "sold_qty": 1,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=slow_movers)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    
    def mock_session_local():
        return mock_session
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", mock_session_local)
    
    result = compute_slow_movers(shop_id="shop-1")
    
    assert result == 1


def test_compute_slow_movers_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test slow movers with no products."""
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=[])
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = compute_slow_movers()
    
    assert result == 0


def test_nightly_snapshot_with_multiple_shops(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test nightly snapshot with sales from multiple shops."""
    snapshot_data = [
        {
            "shop_id": "shop-1",
            "total_sales": 10,
            "total_revenue": 1000.0,
        },
        {
            "shop_id": "shop-2",
            "total_sales": 5,
            "total_revenue": 500.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=snapshot_data)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = nightly_snapshot()
    
    assert result == 2


def test_nightly_snapshot_single_shop(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test nightly snapshot for single shop."""
    snapshot_data = [
        {
            "shop_id": "shop-1",
            "total_sales": 20,
            "total_revenue": 2000.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=snapshot_data)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = nightly_snapshot()
    
    assert result == 1


def test_nightly_snapshot_no_sales(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test nightly snapshot with no sales."""
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=[])
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = nightly_snapshot()
    
    assert result == 0


def test_ingest_sale_event_zero_amount(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test sale event ingestion with zero amount."""
    sale_row = {
        "id": "sale-0",
        "shop_id": "shop-1",
        "sale_number": "SAL-000",
        "total_amount": 0.0,
        "created_at": "2026-02-20",
    }
    items = []
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=sale_row)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=items)
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-2")
    
    result = ingest_sale_event("sale-0", "shop-1", "corr-000")
    
    assert result["total_amount"] == 0.0
    assert result["items"] == []


def test_ingest_sale_event_multiple_items(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test sale event ingestion with multiple items."""
    sale_row = {
        "id": "sale-multi",
        "shop_id": "shop-1",
        "sale_number": "SAL-100",
        "total_amount": 1500.0,
        "created_at": "2026-02-20",
    }
    items = [
        {
            "product_id": "prod-1",
            "quantity": 5,
            "unit_price": 100.0,
            "line_total": 500.0,
        },
        {
            "product_id": "prod-2",
            "quantity": 10,
            "unit_price": 75.0,
            "line_total": 750.0,
        },
        {
            "product_id": "prod-3",
            "quantity": 2,
            "unit_price": 125.0,
            "line_total": 250.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=sale_row)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=items)
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-3")
    
    result = ingest_sale_event("sale-multi", "shop-1", "corr-multi")
    
    assert result["event_type"] == "sale_ingested"
    assert result["total_amount"] == 1500.0
    assert len(result["items"]) == 3
    assert result["items"][0]["product_id"] == "prod-1"
    assert result["items"][1]["quantity"] == 10
    assert result["items"][2]["line_total"] == 250.0


def test_ingest_sale_event_large_amount(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test sale event ingestion with large transaction amount."""
    sale_row = {
        "id": "sale-large",
        "shop_id": "shop-premium",
        "sale_number": "SAL-9999",
        "total_amount": 99999.99,
        "created_at": "2026-02-20",
    }
    items = [
        {
            "product_id": "prod-luxury",
            "quantity": 1,
            "unit_price": 99999.99,
            "line_total": 99999.99,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=sale_row)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=items)
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-4")
    
    result = ingest_sale_event("sale-large", "shop-premium", "corr-large")
    
    assert result["total_amount"] == 99999.99
    assert result["shop_id"] == "shop-premium"


def test_ingest_sale_event_commit_called(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that database commit is called during sale ingestion."""
    sale_row = {
        "id": "sale-commit",
        "shop_id": "shop-1",
        "sale_number": "SAL-COMMIT",
        "total_amount": 100.0,
        "created_at": "2026-02-20",
    }
    items = []
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=sale_row)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=items)
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-5")
    
    ingest_sale_event("sale-commit", "shop-1", "corr-commit")
    
    assert mock_session.commit.called


def test_ingest_sale_event_correlation_id_propagated(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that correlation ID is properly propagated in event."""
    sale_row = {
        "id": "sale-corr",
        "shop_id": "shop-1",
        "sale_number": "SAL-CORR",
        "total_amount": 200.0,
        "created_at": "2026-02-20",
    }
    items = []
    correlation_id = "corr-unique-12345"
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=sale_row)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=items)
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-6")
    
    result = ingest_sale_event("sale-corr", "shop-1", correlation_id)
    
    assert result["correlation_id"] == correlation_id


def test_stream_inventory_event_with_large_quantity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test inventory event streaming with large quantity."""
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "2-2")
    
    result = stream_inventory_event(
        shop_id="shop-1",
        product_id="prod-bulk",
        movement_type="addition",
        quantity=10000,
        correlation_id="corr-bulk"
    )
    
    assert result["quantity"] == 10000
    assert result["product_id"] == "prod-bulk"


def test_stream_inventory_event_zero_quantity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test inventory event streaming with zero quantity."""
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "2-3")
    
    result = stream_inventory_event(
        shop_id="shop-1",
        product_id="prod-0",
        movement_type="adjustment",
        quantity=0,
        correlation_id="corr-zero"
    )
    
    assert result["quantity"] == 0
    assert result["event_type"] == "inventory_stream"


def test_stream_inventory_event_all_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test inventory event contains all required fields."""
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "2-4")
    
    result = stream_inventory_event(
        shop_id="shop-test",
        product_id="prod-test",
        movement_type="removal",
        quantity=25,
        correlation_id="corr-test"
    )
    
    assert "event_type" in result
    assert "shop_id" in result
    assert "product_id" in result
    assert "movement_type" in result
    assert "quantity" in result
    assert "correlation_id" in result
    assert result["shop_id"] == "shop-test"
    assert result["product_id"] == "prod-test"


def test_compute_slow_movers_boundary_condition(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test slow movers with products at boundary (exactly 5 sold)."""
    slow_movers = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-boundary",
            "name": "Boundary Product",
            "sold_qty": 4,  # Less than 5, should be included
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=slow_movers)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = compute_slow_movers()
    
    assert result == 1


def test_compute_slow_movers_multiple_shops(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test slow movers across multiple shops."""
    slow_movers = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Slow Product Shop1",
            "sold_qty": 1,
        },
        {
            "shop_id": "shop-2",
            "product_id": "prod-2",
            "name": "Slow Product Shop2",
            "sold_qty": 2,
        },
        {
            "shop_id": "shop-3",
            "product_id": "prod-3",
            "name": "Slow Product Shop3",
            "sold_qty": 0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=slow_movers)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = compute_slow_movers()
    
    assert result == 3


def test_compute_slow_movers_large_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test slow movers computation with large dataset."""
    slow_movers = [
        {
            "shop_id": f"shop-{i}",
            "product_id": f"prod-{i}",
            "name": f"Slow Product {i}",
            "sold_qty": i % 5,
        }
        for i in range(100)
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=slow_movers)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = compute_slow_movers()
    
    assert result == 100


def test_nightly_snapshot_payload_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that nightly snapshot payload has correct structure."""
    snapshot_data = [
        {
            "shop_id": "shop-payload",
            "total_sales": 15,
            "total_revenue": 1500.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=snapshot_data)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = nightly_snapshot()
    
    assert result == 1
    # Verify that execute was called for both select and insert
    assert mock_session.execute.call_count == 2


def test_nightly_snapshot_with_large_revenue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test nightly snapshot with very large revenue amounts."""
    snapshot_data = [
        {
            "shop_id": "shop-large",
            "total_sales": 1000,
            "total_revenue": 999999.99,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=snapshot_data)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = nightly_snapshot()
    
    assert result == 1


def test_nightly_snapshot_commits_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that nightly snapshot commits database changes."""
    snapshot_data = [
        {
            "shop_id": "shop-commit",
            "total_sales": 5,
            "total_revenue": 500.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=snapshot_data)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    nightly_snapshot()
    
    assert mock_session.commit.called


def test_nightly_snapshot_zero_sales_shop(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test nightly snapshot with shop having zero sales but revenue."""
    snapshot_data = [
        {
            "shop_id": "shop-zero-sales",
            "total_sales": 0,
            "total_revenue": 0.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=snapshot_data)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = nightly_snapshot()
    
    assert result == 1


def test_nightly_snapshot_mixed_revenue_amounts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test nightly snapshot with shops having varying revenue amounts."""
    snapshot_data = [
        {
            "shop_id": "shop-high",
            "total_sales": 50,
            "total_revenue": 5000.0,
        },
        {
            "shop_id": "shop-medium",
            "total_sales": 20,
            "total_revenue": 1000.0,
        },
        {
            "shop_id": "shop-low",
            "total_sales": 5,
            "total_revenue": 250.0,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all = Mock(return_value=snapshot_data)
    
    mock_execute.return_value = mock_result
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    
    result = nightly_snapshot()
    
    assert result == 3


def test_ingest_sale_event_type_conversions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ingest_sale_event properly converts data types."""
    sale_row = {
        "id": "sale-types",
        "shop_id": "shop-types",
        "sale_number": "SAL-TYPES",
        "total_amount": 333.33,
        "created_at": "2026-02-20",
    }
    items = [
        {
            "product_id": "prod-type-test",
            "quantity": 3,
            "unit_price": 111.11,
            "line_total": 333.33,
        }
    ]
    
    mock_session = Mock()
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    mock_execute = Mock()
    mock_result1 = Mock()
    mock_result1.mappings.return_value.first = Mock(return_value=sale_row)
    mock_result2 = Mock()
    mock_result2.mappings.return_value.all = Mock(return_value=items)
    
    mock_result3 = Mock()
    mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]
    mock_session.execute = mock_execute
    mock_session.commit = Mock()
    
    monkeypatch.setattr("app.workers.tasks.analytics.SessionLocal", lambda: mock_session)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client.xadd", lambda *_args, **_kwargs: "1-7")
    
    result = ingest_sale_event("sale-types", "shop-types", "corr-types")
    
    # Verify type conversions
    assert isinstance(result["sale_id"], str)
    assert isinstance(result["shop_id"], str)
    assert isinstance(result["total_amount"], float)
    assert isinstance(result["items"][0]["quantity"], int)
    assert isinstance(result["items"][0]["unit_price"], float)
    assert isinstance(result["items"][0]["line_total"], float)
