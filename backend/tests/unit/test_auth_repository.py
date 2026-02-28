import pytest

from app.modules.auth.repository import auth_repository


class DummyResult:
    def __init__(self, rowcount: int = 0, row=None):
        self.rowcount = rowcount
        self._row = row or {}

    def mappings(self):
        return self

    def first(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.executed = []

    def execute(self, stmt, params=None):
        # record executed statement and parameters for inspection
        self.executed.append((str(stmt), params))
        text = str(stmt).upper()
        if text.strip().startswith("SELECT"):
            # simulate a lookup result
            return DummyResult(row={"jti": params.get("jti"), "user_id": "u1", "revoked_at": None})
        if text.strip().startswith("UPDATE"):
            # return a result with rowcount
            return DummyResult(rowcount=1)
        return DummyResult()


def test_create_and_get_refresh_session():
    db = DummyDB()
    auth_repository.create_refresh_session(db, "j1", "u1", 123, "ua", "ip")
    assert db.executed, "execute should have been called"
    # now call get and expect the mapping
    result = auth_repository.get_refresh_session(db, "j1")
    assert result["jti"] == "j1"
    assert result["user_id"] == "u1"


def test_revoke_refresh_session():
    db = DummyDB()
    # the dummy returns rowcount=1
    count = auth_repository.revoke_refresh_session(db, "j1")
    assert count == 1
    # simulate already revoked (rowcount 0)
    class ZeroDB(DummyDB):
        def execute(self, stmt, params=None):
            return DummyResult(rowcount=0)

    count2 = auth_repository.revoke_refresh_session(ZeroDB(), "j1")
    assert count2 == 0


def test_revoke_all_user_sessions():
    db = DummyDB()
    auth_repository.revoke_all_user_sessions(db, "u1")
    assert any("UPDATE refresh_token_sessions" in stmt for stmt, _ in db.executed)
