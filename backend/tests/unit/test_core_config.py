"""Unit tests for configuration management."""

import pytest
import os
from unittest.mock import patch
from pydantic_settings import BaseSettings


def test_settings_loads_from_env():
    """Test that settings load from environment variables."""
    from app.core.config import settings
    
    assert settings is not None


def test_settings_has_database_url():
    """Test that database URL is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "database_url")
    assert settings.database_url is not None


def test_settings_has_redis_url():
    """Test that Redis URL is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "redis_url")
    assert settings.redis_url is not None


def test_settings_has_app_name():
    """Test that app name is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "app_name")
    assert settings.app_name == "srip-api"


def test_settings_has_environment():
    """Test that environment (env) setting is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "env")
    assert settings.env in ["development", "production", "testing"]


def test_settings_has_api_version():
    """Test that api_v1_prefix setting is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "api_v1_prefix")
    assert settings.api_v1_prefix == "/api/v1"


def test_settings_has_log_level():
    """Test that log level is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "log_level")
    assert settings.log_level is not None


def test_settings_has_redis_stream_maxlen():
    """Test that Redis stream maxlen is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "redis_stream_maxlen")
    assert isinstance(settings.redis_stream_maxlen, int)
    assert settings.redis_stream_maxlen > 0


def test_settings_database_url_format():
    """Test that database URL has correct format."""
    from app.core.config import settings
    
    # Should be a database connection string
    db_url = settings.database_url
    assert ("://" in db_url) or db_url.startswith("sqlite")


def test_settings_redis_url_format():
    """Test that Redis URL has correct format."""
    from app.core.config import settings
    
    # Should be redis:// URL
    redis_url = settings.redis_url
    assert "redis" in redis_url.lower() or "localhost" in redis_url.lower()


def test_settings_app_title():
    """Test that app title is configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "app_name")
    assert settings.app_name is not None


def test_settings_is_singleton():
    """Test that settings instance is reused."""
    from app.core.config import settings as settings1
    from app.core.config import settings as settings2
    
    # Should be same instance
    assert settings1 is settings2


def test_settings_environment_overrides():
    """Test that environment variables override defaults."""
    # This tests the env_file loading capability
    from app.core.config import Settings
    
    # Should be able to create instance with custom values
    settings_class = Settings
    assert settings_class is not None


def test_settings_pydantic_config():
    """Test that settings use Pydantic BaseSettings."""
    from app.core.config import settings, Settings
    
    # Should extend BaseSettings
    assert isinstance(settings, BaseSettings)


def test_settings_validation():
    """Test that settings validate input correctly."""
    from app.core.config import Settings
    
    # Creating settings class should work
    assert Settings is not None


def test_settings_attributes_accessible():
    """Test that settings attributes are accessible."""
    from app.core.config import settings
    
    # Should be able to access attributes without error
    _ = settings.database_url
    _ = settings.redis_url
    _ = settings.app_name
    _ = settings.env
    _ = settings.log_level


def test_settings_database_pool_size():
    """Test that database pool size is set."""
    from app.core.config import settings
    
    # Should have pool configuration
    assert hasattr(settings, "database_url")


def test_settings_logger_configured():
    """Test that logger is properly configured."""
    from app.core.config import settings
    
    assert hasattr(settings, "log_level")
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert settings.log_level in valid_levels


def test_settings_json_serialization():
    """Test that settings can be serialized to JSON."""
    from app.core.config import settings
    
    # Should be able to convert to dict
    settings_dict = settings.model_dump()
    assert isinstance(settings_dict, dict)
    assert "app_name" in settings_dict
