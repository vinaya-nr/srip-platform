import pytest
from datetime import date

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.notifications.service import notification_service
from app.modules.notifications.schemas import NotificationCreateSchema


class StubNotification:
    def __init__(self, id: str = "n1", shop_id: str = "s1", is_read: bool = False) -> None:
        self.id = id
        self.shop_id = shop_id
        self.event_type = "evt"
        self.title = "T"
        self.message = "M"
        self.is_read = is_read
        from datetime import datetime

        self.created_at = datetime.utcnow()


def test_create_and_list_notifications(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = StubNotification()
    monkeypatch.setattr("app.modules.notifications.repository.notification_repository.create", lambda *_: stub)
    monkeypatch.setattr(
        "app.modules.notifications.repository.notification_repository.list",
        lambda *_args, **_kwargs: ([stub], 1),
    )

    created = notification_service.create(None, "s1", NotificationCreateSchema(event_type="x", title="t", message="m"))
    assert created.id == "n1"

    listed = notification_service.list(None, "s1", unread_only=True)
    assert len(listed.items) == 1
    assert listed.items[0].is_read is False


def test_mark_read_success_and_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = StubNotification(is_read=False)
    monkeypatch.setattr("app.modules.notifications.repository.notification_repository.get", lambda *_: stub)
    monkeypatch.setattr("app.modules.notifications.repository.notification_repository.mark_read", lambda *_: (setattr(stub, "is_read", True), stub)[1])

    updated = notification_service.mark_read(None, "s1", "n1")
    assert updated.is_read is True

    monkeypatch.setattr("app.modules.notifications.repository.notification_repository.get", lambda *_: None)
    with pytest.raises(NotFoundException):
        notification_service.mark_read(None, "s1", "missing")


def test_list_notifications_invalid_date_range(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationException):
        notification_service.list(
            None,
            "s1",
            unread_only=False,
            from_date=date(2026, 2, 27),
            to_date=date(2026, 2, 26),
        )


def test_list_notifications_passes_date_filters_to_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = StubNotification()
    captured: dict[str, object] = {}

    def fake_list(_db, shop_id, unread_only, skip, limit, from_date, to_date):
        captured["shop_id"] = shop_id
        captured["unread_only"] = unread_only
        captured["skip"] = skip
        captured["limit"] = limit
        captured["from_date"] = from_date
        captured["to_date"] = to_date
        return [stub], 1

    monkeypatch.setattr("app.modules.notifications.repository.notification_repository.list", fake_list)

    result = notification_service.list(
        None,
        "s1",
        unread_only=True,
        skip=5,
        limit=10,
        from_date=date(2026, 2, 1),
        to_date=date(2026, 2, 26),
    )

    assert len(result.items) == 1
    assert captured == {
        "shop_id": "s1",
        "unread_only": True,
        "skip": 5,
        "limit": 10,
        "from_date": date(2026, 2, 1),
        "to_date": date(2026, 2, 26),
    }


def test_notifications_repository_create(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.notifications.repository import notification_repository
    from app.modules.notifications.schemas import NotificationCreateSchema

    class MockDB:
        def add(self, obj):
            pass

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    payload = NotificationCreateSchema(event_type="evt", title="T", message="M")
    notif = notification_repository.create(MockDB(), "s1", payload)
    assert notif.shop_id == "s1"


def test_notifications_repository_list(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.notifications.repository import notification_repository

    notifs = [StubNotification(id="n1"), StubNotification(id="n2", is_read=True)]

    class MockScalars:
        def all(self):
            return notifs

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

        def scalar(self, stmt):
            return 2

    result, total = notification_repository.list(MockDB(), "s1", unread_only=False)
    assert len(result) == 2
    assert total == 2


def test_notifications_repository_list_unread_only(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.notifications.repository import notification_repository

    notifs = [StubNotification(id="n1")]

    class MockScalars:
        def all(self):
            return notifs

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

        def scalar(self, stmt):
            return 1

    result, total = notification_repository.list(MockDB(), "s1", unread_only=True)
    assert len(result) == 1
    assert result[0].is_read is False
    assert total == 1


def test_notifications_repository_get(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.notifications.repository import notification_repository

    class MockDB:
        def scalar(self, stmt):
            return StubNotification()

    result = notification_repository.get(MockDB(), "s1", "n1")
    assert result.id == "n1"


def test_notifications_repository_mark_read(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.notifications.repository import notification_repository

    class MockDB:
        def commit(self):
            pass

        def refresh(self, obj):
            pass

    notif = StubNotification(is_read=False)
    result = notification_repository.mark_read(MockDB(), notif)
    assert result.is_read is True
