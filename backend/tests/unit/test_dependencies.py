"""Tests for core dependencies and health checks."""

import pytest
from app.core.exceptions import AuthorizationException
from app.modules.auth.schemas import CurrentUserSchema


def test_get_current_user_missing_shop_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_current_user when token has no shop_id."""
    def mock_verify_token(*_):
        return type('TokenPayload', (), {'sub': 'u1', 'shop_id': None})()
    
    from app.core.dependencies import get_current_user
    
    monkeypatch.setattr("app.core.dependencies.verify_token", mock_verify_token)
    
    with pytest.raises(AuthorizationException):
        get_current_user("token", None)  # type: ignore[arg-type]


def test_get_current_user_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_current_user when user is not found."""
    def mock_verify_token(*_):
        return type('TokenPayload', (), {'sub': 'u1', 'shop_id': 's1'})()
    
    monkeypatch.setattr("app.core.dependencies.verify_token", mock_verify_token)
    monkeypatch.setattr("app.core.dependencies.user_repository.get_user_by_id", lambda *_: None)
    
    from app.core.dependencies import get_current_user
    
    with pytest.raises(AuthorizationException):
        get_current_user("token", None)  # type: ignore[arg-type]


def test_get_current_user_user_inactive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_current_user when user is inactive."""
    def mock_verify_token(*_):
        return type('TokenPayload', (), {'sub': 'u1', 'shop_id': 's1'})()
    
    inactive_user = type('User', (), {
        'id': 'u1',
        'email': 'user@example.com',
        'shop_id': 's1',
        'is_active': False,
    })()
    
    monkeypatch.setattr("app.core.dependencies.verify_token", mock_verify_token)
    monkeypatch.setattr("app.core.dependencies.user_repository.get_user_by_id", lambda *_: inactive_user)
    
    from app.core.dependencies import get_current_user
    
    with pytest.raises(AuthorizationException):
        get_current_user("token", None)  # type: ignore[arg-type]


def test_get_current_user_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful get_current_user call."""
    def mock_verify_token(*_):
        return type('TokenPayload', (), {'sub': 'u1', 'shop_id': 's1'})()
    
    active_user = type('User', (), {
        'id': 'u1',
        'email': 'user@example.com',
        'shop_id': 's1',
        'is_active': True,
    })()
    
    monkeypatch.setattr("app.core.dependencies.verify_token", mock_verify_token)
    monkeypatch.setattr("app.core.dependencies.user_repository.get_user_by_id", lambda *_: active_user)
    
    from app.core.dependencies import get_current_user
    
    result = get_current_user("token", None)  # type: ignore[arg-type]
    assert isinstance(result, CurrentUserSchema)
    assert result.id == 'u1'


def test_get_current_shop():
    from app.core.dependencies import get_current_shop
    user = CurrentUserSchema(id='u1', email='user@example.com', shop_id='s1')
    assert get_current_shop(user) == 's1'
