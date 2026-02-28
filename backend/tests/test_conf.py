from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def setex(self, key: str, _: int, value: str) -> None:
        self.store[key] = value

    def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

    def delete(self, key: str) -> None:
        self.store.pop(key, None)

    def ping(self) -> bool:
        return True

    def xadd(self, _: str, __: dict, maxlen: int | None = None) -> str:  # noqa: ARG002
        return "1-0"


@pytest.fixture
def dummy_redis(monkeypatch: pytest.MonkeyPatch) -> DummyRedis:
    redis = DummyRedis()
    monkeypatch.setattr("app.core.security.get_redis_client", lambda: redis)
    monkeypatch.setattr("app.workers.tasks.analytics.redis_client", redis)
    return redis


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
