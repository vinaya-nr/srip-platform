"""Tests for health check functions."""

import pytest
from app.core.health import check_postgres, check_redis, check_celery


def test_check_postgres_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test postgres health check when successful."""
    class MockDB:
        def execute(self, stmt):
            return True
    
    result = check_postgres(MockDB())
    assert result is True


def test_check_postgres_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test postgres health check when failed."""
    class MockDB:
        def execute(self, stmt):
            raise Exception("Connection failed")
    
    result = check_postgres(MockDB())
    assert result is False


def test_check_redis_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test redis health check when successful."""
    class MockRedis:
        def ping(self):
            return True
    
    monkeypatch.setattr("app.core.health.get_redis_client", lambda: MockRedis())
    
    result = check_redis()
    assert result is True


def test_check_redis_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test redis health check when failed."""
    class MockRedis:
        def ping(self):
            raise Exception("Redis unavailable")
    
    monkeypatch.setattr("app.core.health.get_redis_client", lambda: MockRedis())
    
    result = check_redis()
    assert result is False


def test_check_celery_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test celery health check when successful."""
    class MockInspect:
        def ping(self):
            return {"celery@worker": "pong"}
    
    class MockControl:
        def inspect(self, timeout=1.0):
            return MockInspect()
    
    class MockCeleryApp:
        control = MockControl()
    
    monkeypatch.setattr("app.core.health.celery_app", MockCeleryApp())
    
    result = check_celery()
    assert result is True


def test_check_celery_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test celery health check when failed."""
    class MockControl:
        def inspect(self, timeout=1.0):
            raise Exception("Celery unavailable")
    
    class MockCeleryApp:
        control = MockControl()
    
    monkeypatch.setattr("app.core.health.celery_app", MockCeleryApp())
    
    result = check_celery()
    assert result is False
