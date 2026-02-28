"""Unit tests for stock alerts worker tasks."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock
from app.workers.tasks.stock_alerts import check_low_stock, check_expiry_dates


def test_check_low_stock_with_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test low stock detection with alerts created."""
    mock_rows = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Product A",
            "low_stock_threshold": 5,
            "stock": 2,
        }
    ]
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()
        
        # Create different result objects for different queries
        result_low_stock = Mock()
        result_low_stock.mappings.return_value.all.return_value = mock_rows
        
        # Mock for recent alert check (returns None = no recent alerts)
        result_recent_alert = Mock()
        result_recent_alert.first.return_value = None
        
        # Mock for INSERT (doesn't need specific return value)
        result_insert = Mock()
        
        # Side effect to return different results for each execute() call
        # Call 1: SELECT low_stock products
        # Call 2: SELECT recent alerts
        # Call 3: INSERT notification
        session.execute = Mock(side_effect=[result_low_stock, result_recent_alert, result_insert])
        
        return session
    
    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)
    
    result = check_low_stock("shop-1")
    assert result == 1


def test_check_low_stock_for_all_shops(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test low stock detection across all shops."""
    mock_rows = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Product A",
            "low_stock_threshold": 5,
            "stock": 1,
        },
        {
            "shop_id": "shop-2",
            "product_id": "prod-2",
            "name": "Product B",
            "low_stock_threshold": 10,
            "stock": 3,
        }
    ]
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()
        
        # Create different result objects for different queries
        result_low_stock = Mock()
        result_low_stock.mappings.return_value.all.return_value = mock_rows
        
        # For each product, we need results for recent_alert checks and INSERTs
        result_recent_alert1 = Mock()
        result_recent_alert1.first.return_value = None  # No recent alerts
        
        result_insert1 = Mock()  # INSERT for product 1
        
        result_recent_alert2 = Mock()
        result_recent_alert2.first.return_value = None  # No recent alerts
        
        result_insert2 = Mock()  # INSERT for product 2
        
        # Side effect for each execute() call:
        # 1: SELECT low_stock products (returns 2 rows)
        # 2: SELECT recent alerts for product 1
        # 3: INSERT notification for product 1
        # 4: SELECT recent alerts for product 2
        # 5: INSERT notification for product 2
        session.execute = Mock(side_effect=[
            result_low_stock,
            result_recent_alert1,
            result_insert1,
            result_recent_alert2,
            result_insert2
        ])
        
        return session
    
    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)
    
    result = check_low_stock()
    assert result == 2


def test_check_low_stock_no_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test low stock detection with no alerts."""
    mock_db = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all.return_value = []
    
    mock_execute = Mock(return_value=mock_result)
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.execute = mock_execute
        session.commit = Mock()
        return session
    
    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)
    
    result = check_low_stock("shop-1")
    assert result == 0


def test_check_low_stock_query_filters_active_products(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure low stock SQL includes active-product filter."""

    captured_queries: list[str] = []

    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()

        result_low_stock = Mock()
        result_low_stock.mappings.return_value.all.return_value = []

        def fake_execute(stmt, *_args, **_kwargs):
            captured_queries.append(str(stmt))
            return result_low_stock

        session.execute = Mock(side_effect=fake_execute)
        return session

    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)

    result = check_low_stock("shop-1")
    assert result == 0
    assert captured_queries
    assert "p.is_active = true" in captured_queries[0]


def test_check_low_stock_with_recent_alert_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test low stock detection skips alerts due to cooldown period."""
    mock_rows = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Product A",
            "low_stock_threshold": 5,
            "stock": 2,
        }
    ]
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()
        
        # Create different result objects for different queries
        result_low_stock = Mock()
        result_low_stock.mappings.return_value.all.return_value = mock_rows
        
        # Mock recent alert check - this time it DOES exist
        result_recent_alert = Mock()
        result_recent_alert.first.return_value = {"id": "existing-alert-id"}  # Alert exists!
        
        # Side effect for execute() calls
        # Call 1: SELECT low_stock products
        # Call 2: SELECT recent alerts (returns existing alert, so we skip INSERT)
        session.execute = Mock(side_effect=[result_low_stock, result_recent_alert])
        
        return session
    
    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)
    
    result = check_low_stock("shop-1")
    # Should return 0 because alert was skipped due to cooldown
    assert result == 0


def test_check_expiry_dates_with_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test expiry date detection with alerts created."""
    future_date = date.today() + timedelta(days=5)
    mock_rows = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Product A",
            "expiry_date": future_date,
        }
    ]
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()

        result_expiry = Mock()
        result_expiry.mappings.return_value.all.return_value = mock_rows

        result_recent_alert = Mock()
        result_recent_alert.first.return_value = None

        result_insert = Mock()

        session.execute = Mock(side_effect=[result_expiry, result_recent_alert, result_insert])
        return session
    
    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)
    
    result = check_expiry_dates(within_days=15)
    assert result == 1


def test_check_expiry_dates_custom_days(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test expiry date detection with custom days threshold."""
    future_date = date.today() + timedelta(days=30)
    mock_rows = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Product A",
            "expiry_date": future_date,
        }
    ]
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()

        result_expiry = Mock()
        result_expiry.mappings.return_value.all.return_value = mock_rows

        result_recent_alert = Mock()
        result_recent_alert.first.return_value = None

        result_insert = Mock()

        session.execute = Mock(side_effect=[result_expiry, result_recent_alert, result_insert])
        return session
    
    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)
    
    result = check_expiry_dates(within_days=30)
    assert result == 1


def test_check_expiry_dates_no_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test expiry date detection with no alerts."""
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()

        result_expiry = Mock()
        result_expiry.mappings.return_value.all.return_value = []

        session.execute = Mock(return_value=result_expiry)
        return session
    
    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)
    
    result = check_expiry_dates()
    assert result == 0


def test_check_expiry_query_filters_active_and_positive_quantity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure expiry SQL includes active-product and positive-quantity filters."""

    captured_queries: list[str] = []

    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()

        result_expiry = Mock()
        result_expiry.mappings.return_value.all.return_value = []

        def fake_execute(stmt, *_args, **_kwargs):
            captured_queries.append(str(stmt))
            return result_expiry

        session.execute = Mock(side_effect=fake_execute)
        return session

    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)

    result = check_expiry_dates(within_days=15)
    assert result == 0
    assert captured_queries
    assert "b.quantity > 0" in captured_queries[0]
    assert "p.is_active = true" in captured_queries[0]


def test_check_expiry_dates_with_recent_alert_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test expiry date detection skips alerts due to cooldown period."""
    future_date = date.today() + timedelta(days=3)
    mock_rows = [
        {
            "shop_id": "shop-1",
            "product_id": "prod-1",
            "name": "Product A",
            "expiry_date": future_date,
        }
    ]

    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.commit = Mock()

        result_expiry = Mock()
        result_expiry.mappings.return_value.all.return_value = mock_rows

        result_recent_alert = Mock()
        result_recent_alert.first.return_value = {"id": "existing-expiry-alert-id"}

        session.execute = Mock(side_effect=[result_expiry, result_recent_alert])
        return session

    monkeypatch.setattr("app.workers.tasks.stock_alerts.SessionLocal", mock_session_local)

    result = check_expiry_dates(within_days=15)
    assert result == 0
