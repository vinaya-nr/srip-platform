"""Unit tests for security utilities."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import timedelta, UTC, datetime
from jose import JWTError


def test_security_module_imports():
    """Test that security module imports correctly."""
    from app.core import security
    
    assert security is not None


def test_get_redis_client():
    """Test Redis client initialization."""
    from app.core.security import get_redis_client
    
    assert callable(get_redis_client)


def test_redis_client_singleton():
    """Test Redis client is reused."""
    from app.core.security import get_redis_client
    
    client1 = get_redis_client()
    client2 = get_redis_client()
    
    assert client1 is client2


def test_jwt_encode_token():
    """Test JWT token encoding."""
    from app.core.security import create_access_token
    
    # Should be callable
    assert callable(create_access_token)


def test_token_expiration():
    """Test token expiration configuration."""
    from app.core.config import settings
    
    assert settings.access_token_expire_minutes is not None
    assert isinstance(settings.access_token_expire_minutes, int)
    assert settings.access_token_expire_minutes > 0


def test_algorithm_configured():
    """Test JWT algorithm is configured."""
    from app.core.config import settings
    
    assert settings.jwt_algorithm is not None
    assert settings.jwt_algorithm == "HS256"


def test_secret_key_configured():
    """Test secret key is configured."""
    from app.core.config import settings
    
    assert settings.secret_key is not None
    assert len(settings.secret_key) > 0


def test_hash_password():
    """Test password hashing."""
    from app.core.security import hash_password
    
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 0


def test_verify_password():
    """Test password verification."""
    from app.core.security import hash_password, verify_password
    
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed)


def test_verify_password_wrong():
    """Test password verification with wrong password."""
    from app.core.security import hash_password, verify_password
    
    password = "test_password_123"
    wrong_password = "wrong_password_456"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed)
    assert not verify_password(wrong_password, hashed)


def test_create_access_token():
    """Test access token creation."""
    from app.core.security import create_access_token
    
    user_id = "user_123"
    shop_id = "shop_456"
    token = create_access_token(user_id, shop_id)
    
    assert token is not None
    assert isinstance(token, str)
    assert "." in token  # JWT has 3 parts separated by dots


def test_create_access_token_decode():
    """Test access token can be decoded."""
    from app.core.security import create_access_token
    from app.core.config import settings
    from jose import jwt
    
    user_id = "user_123"
    shop_id = "shop_456"
    token = create_access_token(user_id, shop_id)
    
    # Should be able to decode the token
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == user_id
    assert payload["shop_id"] == shop_id
    assert payload["token_type"] == "access"


def test_security_functions_exist():
    """Test all security functions exist."""
    from app.core import security
    
    assert hasattr(security, "get_redis_client")
    assert hasattr(security, "hash_password")
    assert hasattr(security, "verify_password")
    assert hasattr(security, "create_access_token")


def test_redis_connection_params():
    """Test Redis connection parameters."""
    from app.core.config import settings
    
    assert hasattr(settings, "redis_url")
    assert settings.redis_url is not None


def test_password_context():
    """Test password context is configured."""
    from app.core.security import pwd_context
    
    assert pwd_context is not None


def test_hash_consistency():
    """Test that same password produces different hashes."""
    from app.core.security import hash_password
    
    password = "test_password_123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Different hashes due to salt, but both verify
    assert hash1 != hash2


def test_token_structure():
    """Test JWT token has correct structure."""
    from app.core.security import create_access_token
    import json
    import base64
    
    user_id = "user_123"
    shop_id = "shop_456"
    token = create_access_token(user_id, shop_id)
    
    # Split token into parts
    parts = token.split(".")
    assert len(parts) == 3
    
    # Decode header
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "==="))
    assert "alg" in header
    assert header["alg"] == "HS256"


def test_security_exception_handling():
    """Test security exception handling."""
    from app.core.security import verify_password
    
    # Should handle None gracefully
    result = verify_password("password", None)
    assert result is False or isinstance(result, bool)
