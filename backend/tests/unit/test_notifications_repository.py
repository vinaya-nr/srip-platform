import pytest
from datetime import datetime

from app.modules.notifications.schemas import NotificationCreateSchema


class StubNotification:
    def __init__(self, id: str = "n1", shop_id: str = "s1", is_read: bool = False):
        self.id = id
        self.shop_id = shop_id
        self.event_type = "event"
        self.title = "Title"
        self.message = "Message"
        self.is_read = is_read
        self.created_at = datetime.utcnow()


def test_notifications_repository_create(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.notifications.repository import notification_repository

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
