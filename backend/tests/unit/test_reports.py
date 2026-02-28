"""Unit tests for reports worker tasks."""

import pytest
from datetime import date
from unittest.mock import Mock, patch
from app.workers.tasks.reports import generate_daily_report, monthly_summary


def test_generate_daily_report_with_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test daily report generation with sales data."""
    mock_row = {
        "total_sales": 5,
        "total_revenue": 150.0,
    }
    
    mock_db = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.first.return_value = mock_row
    
    mock_execute = Mock(return_value=mock_result)
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.execute = mock_execute
        return session
    
    monkeypatch.setattr("app.workers.tasks.reports.SessionLocal", mock_session_local)
    
    result = generate_daily_report("shop-1")
    
    assert result["shop_id"] == "shop-1"
    assert result["total_sales"] == 5
    assert result["total_revenue"] == 150.0
    assert result["date"] == str(date.today())


def test_generate_daily_report_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test daily report generation with no sales data."""
    mock_db = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.first.return_value = None
    
    mock_execute = Mock(return_value=mock_result)
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.execute = mock_execute
        return session
    
    monkeypatch.setattr("app.workers.tasks.reports.SessionLocal", mock_session_local)
    
    result = generate_daily_report("shop-1")
    
    assert result["total_sales"] == 0
    assert result["total_revenue"] == 0.0


def test_monthly_summary_with_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test monthly summary generation with data."""
    mock_rows = [
        {
            "shop_id": "shop-1",
            "month_bucket": "2026-02-01",
            "total_sales": 10,
            "total_revenue": 1000.0,
        }
    ]
    
    mock_db = Mock()
    mock_result = Mock()
    mock_result.mappings.return_value.all.return_value = mock_rows
    
    mock_execute = Mock(return_value=mock_result)
    
    def mock_session_local():
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        session.execute = mock_execute
        session.commit = Mock()
        return session
    
    monkeypatch.setattr("app.workers.tasks.reports.SessionLocal", mock_session_local)
    
    result = monthly_summary()
    assert result == 1


def test_monthly_summary_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test monthly summary with no data."""
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
    
    monkeypatch.setattr("app.workers.tasks.reports.SessionLocal", mock_session_local)
    
    result = monthly_summary()
    assert result == 0
