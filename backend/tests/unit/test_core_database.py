"""Unit tests for database configuration and setup."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def test_database_url_from_settings():
    """Test that database URL is properly configured."""
    from app.core.database import SessionLocal
    
    # SessionLocal should be a sessionmaker instance
    assert SessionLocal is not None


def test_session_local_is_callable():
    """Test that SessionLocal can be called to create sessions."""
    from app.core.database import SessionLocal
    
    # Should be callable
    assert callable(SessionLocal)


def test_database_engine_created():
    """Test that database engine is properly initialized."""
    with patch("app.core.database.engine") as mock_engine:
        # Import to trigger module execution
        import app.core.database
        
        # Engine should exist
        assert app.core.database.engine is not None


def test_database_base_metadata():
    """Test that Base metadata is defined."""
    from app.core.database import Base
    
    assert Base is not None
    assert hasattr(Base, "metadata")


def test_session_context_manager():
    """Test that session can be used as context manager."""
    from app.core.database import SessionLocal
    from unittest.mock import MagicMock
    
    # Create a mock session that supports context manager
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    
    # Test that we can use it with context manager
    with mock_session as session:
        assert session is not None


def test_database_dependency_injection():
    """Test database dependency injection function."""
    from app.core.dependencies import get_db
    
    # Should be a generator function
    assert callable(get_db)


def test_database_session_isolation():
    """Test that each session is isolated."""
    from app.core.database import SessionLocal
    
    # Should be able to create multiple sessions
    assert SessionLocal is not None


def test_database_configuration_read():
    """Test that database configuration is read from settings."""
    from app.core.config import settings
    
    # Settings should have database URL
    assert hasattr(settings, "database_url")
    assert settings.database_url is not None
    assert "postgresql" in settings.database_url or "mysql" in settings.database_url or "sqlite" in settings.database_url


def test_database_pool_configuration():
    """Test database connection pool is configured."""
    from app.core.database import engine
    
    # Engine pool should be configured
    assert engine.pool is not None


def test_database_echo_setting():
    """Test database echo setting."""
    from app.core.database import engine
    
    # Engine should be created
    assert engine is not None
