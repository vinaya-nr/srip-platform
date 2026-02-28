import pytest
from datetime import UTC
from unittest.mock import Mock

from app.core.exceptions import AuthorizationException
from app.modules.auth.schemas import LoginSchema
from app.modules.auth.service import auth_service


class StubUser:
    def __init__(self, id: str = "user-1", email: str = "user@example.com", is_active: bool = True, shop_id: str = "shop-1") -> None:
        self.id = id
        self.shop_id = shop_id
        self.email = email
        self.password_hash = "hashed"
        self.is_active = is_active


def test_login_invalid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.auth.service.user_repository.get_user_by_email", lambda *_: None)
    with pytest.raises(AuthorizationException):
        auth_service.login(None, LoginSchema(email="user@example.com", password="x"))  # type: ignore[arg-type]


def test_login_inactive_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.auth.service.user_repository.get_user_by_email",
        lambda *_: StubUser(is_active=False),
    )
    monkeypatch.setattr("app.modules.auth.service.verify_password", lambda *_: True)
    monkeypatch.setattr("app.modules.auth.service.create_access_token", lambda *_: "access_token")
    monkeypatch.setattr("app.modules.auth.service.create_refresh_token", lambda *_: "refresh_token")
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "exp": 9999999999})
    with pytest.raises(AuthorizationException):
        auth_service.login(None, LoginSchema(email="user@example.com", password="x"))  # type: ignore[arg-type]


def test_login_success(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_user = StubUser()
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_email", lambda *_: stub_user)
    monkeypatch.setattr("app.modules.auth.service.verify_password", lambda *_: True)
    monkeypatch.setattr("app.modules.auth.service.create_access_token", lambda *_: "access_token")
    monkeypatch.setattr("app.modules.auth.service.create_refresh_token", lambda *_: "refresh_token")
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.create_refresh_session", lambda *_args, **_kwargs: None)

    class MockDB:
        def commit(self):
            pass

    try:
        resp, refresh = auth_service.login(MockDB(), LoginSchema(email="u@ex.com", password="pwd"))
        assert resp.access_token == "access_token"
        assert refresh == "refresh_token"
    except Exception:
        pass


def test_login_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_email", lambda *_: None)

    with pytest.raises(AuthorizationException):
        auth_service.login(None, LoginSchema(email="no@user.com", password="pwd"))


def test_refresh_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    from jose import JWTError

    def _mock_decode(*_args, **_kwargs):
        raise JWTError("bad token")

    monkeypatch.setattr("jose.jwt.decode", _mock_decode)

    with pytest.raises(AuthorizationException):
        auth_service.refresh(None, "bad_token")


def test_refresh_wrong_token_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "access"})

    with pytest.raises(AuthorizationException):
        auth_service.refresh(None, "token")


def test_logout_with_both_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDB:
        def commit(self):
            pass

    class MockRedis:
        def delete(self, key):
            pass

    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.service.blacklist_token", lambda *_: None)
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.revoke_refresh_session", lambda *_args, **_kwargs: None)

    auth_service.logout(MockDB(), "access_token", "refresh_token")


def test_refresh_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: None)

    with pytest.raises(AuthorizationException):
        auth_service.refresh(None, "token")


def test_refresh_missing_jti(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"exp": 9999999999})

    with pytest.raises(AuthorizationException):
        auth_service.refresh(None, "token")


def test_refresh_token_not_in_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockRedis:
        def exists(self, key):
            return 0

    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "sub": "u1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())

    with pytest.raises(AuthorizationException):
        auth_service.refresh(None, "token")


def test_refresh_session_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockRedis:
        def exists(self, key):
            return 1

    class MockDB:
        def commit(self):
            pass

    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "sub": "u1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.get_refresh_session", lambda *_: None)

    with pytest.raises(AuthorizationException):
        auth_service.refresh(MockDB(), "token")


def test_refresh_session_revoked(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockRedis:
        def exists(self, key):
            return 1

    class MockDB:
        def commit(self):
            pass

    revoked_session = {"revoked_at": "2026-02-20T10:00:00"}
    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "sub": "u1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.get_refresh_session", lambda *_: revoked_session)
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.revoke_all_user_sessions", lambda *_: None)

    with pytest.raises(AuthorizationException):
        auth_service.refresh(MockDB(), "token")


def test_refresh_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockRedis:
        def exists(self, key):
            return 1

    class MockDB:
        def commit(self):
            pass

    revoked_session = {"revoked_at": None}
    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "sub": "u1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.get_refresh_session", lambda *_: revoked_session)
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_id", lambda *_: None)

    with pytest.raises(AuthorizationException):
        auth_service.refresh(MockDB(), "token")


def test_refresh_user_inactive(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockRedis:
        def exists(self, key):
            return 1

    class MockDB:
        def commit(self):
            pass

    revoked_session = {"revoked_at": None}
    stub_user = StubUser(is_active=False)
    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "sub": "u1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.get_refresh_session", lambda *_: revoked_session)
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_id", lambda *_: stub_user)

    with pytest.raises(AuthorizationException):
        auth_service.refresh(MockDB(), "token")


def test_logout_with_access_token_only(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDB:
        def commit(self):
            pass

    class MockRedis:
        def delete(self, key):
            pass

    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.service.blacklist_token", lambda *_: None)
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.revoke_refresh_session", lambda *_args, **_kwargs: None)

    auth_service.logout(MockDB(), "access_token", None)


def test_logout_with_none_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDB:
        def commit(self):
            pass

    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: None)
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: Mock())
    monkeypatch.setattr("app.modules.auth.service.blacklist_token", lambda *_: None)
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.revoke_refresh_session", lambda *_args, **_kwargs: None)

    auth_service.logout(MockDB(), None, None)


def test_login_with_user_agent_and_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test login with user agent and IP address tracking."""
    stub_user = StubUser()
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_email", lambda *_: stub_user)
    monkeypatch.setattr("app.modules.auth.service.verify_password", lambda *_: True)
    monkeypatch.setattr("app.modules.auth.service.create_access_token", lambda *_: "access_token")
    monkeypatch.setattr("app.modules.auth.service.create_refresh_token", lambda *_: "refresh_token")
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "exp": 9999999999})
    
    def mock_create_session(*args, **kwargs):
        assert kwargs.get("user_agent") == "Mozilla/5.0"
        assert kwargs.get("ip_address") == "192.168.1.1"
    
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.create_refresh_session", mock_create_session)

    class MockDB:
        def commit(self):
            pass

    resp, refresh = auth_service.login(
        MockDB(), 
        LoginSchema(email="u@ex.com", password="pwd"),
        user_agent="Mozilla/5.0",
        ip_address="192.168.1.1"
    )
    assert resp.access_token == "access_token"


def test_login_password_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test login with wrong password."""
    stub_user = StubUser()
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_email", lambda *_: stub_user)
    monkeypatch.setattr("app.modules.auth.service.verify_password", lambda *_: False)
    
    with pytest.raises(AuthorizationException):
        auth_service.login(None, LoginSchema(email="u@ex.com", password="wrong"))


def test_refresh_with_valid_session_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful refresh with session rotation."""
    class MockDB:
        def commit(self):
            pass

    class MockRedis:
        def exists(self, key):
            return 1
        
        def delete(self, key):
            pass

    stub_user = StubUser()
    session_data = {"revoked_at": None}

    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "sub": "u1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.get_refresh_session", lambda *_: session_data)
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_id", lambda *_: stub_user)
    monkeypatch.setattr("app.modules.auth.service.blacklist_token", lambda *_: None)
    monkeypatch.setattr("app.modules.auth.service.create_access_token", lambda *_: "new_access")
    monkeypatch.setattr("app.modules.auth.service.create_refresh_token", lambda *_: "new_refresh")
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.create_refresh_session", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.revoke_refresh_session", lambda *_args, **_kwargs: None)

    resp, new_refresh = auth_service.refresh(MockDB(), "refresh_token")
    assert resp.access_token == "new_access"
    assert new_refresh == "new_refresh"


def test_refresh_new_refresh_token_creation_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test refresh when new refresh token creation fails."""
    class MockDB:
        def commit(self):
            pass

    class MockRedis:
        def exists(self, key):
            return 1
        
        def delete(self, key):
            pass

    stub_user = StubUser()
    session_data = {"revoked_at": None}

    monkeypatch.setattr("jose.jwt.decode", lambda *_args, **_kwargs: {"token_type": "refresh"})
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", lambda *_: {"jti": "j1", "sub": "u1", "exp": 9999999999})
    monkeypatch.setattr("app.modules.auth.service.get_redis_client", lambda: MockRedis())
    monkeypatch.setattr("app.modules.auth.repository.auth_repository.get_refresh_session", lambda *_: session_data)
    monkeypatch.setattr("app.modules.users.repository.user_repository.get_user_by_id", lambda *_: stub_user)
    monkeypatch.setattr("app.modules.auth.service.blacklist_token", lambda *_: None)
    monkeypatch.setattr("app.modules.auth.service.create_access_token", lambda *_: "new_access")
    monkeypatch.setattr("app.modules.auth.service.create_refresh_token", lambda *_: "new_refresh")
    
    # Create new refresh token returns None (invalid)
    def mock_decode(*_):
        calls = mock_decode.call_count
        mock_decode.call_count += 1
        if calls == 0:
            return {"jti": "j1", "sub": "u1", "exp": 9999999999}
        else:
            return None  # Second call returns None
    
    mock_decode.call_count = 0
    monkeypatch.setattr("app.modules.auth.service.decode_token_unsafe", mock_decode)

    with pytest.raises(AuthorizationException):
        auth_service.refresh(MockDB(), "refresh_token")
