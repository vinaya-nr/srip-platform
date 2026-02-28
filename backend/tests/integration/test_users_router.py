from app.main import app
from app.modules.auth.schemas import CurrentUserSchema

from ..test_conf import client


def test_register_user(client, monkeypatch):  # noqa: ANN001
    monkeypatch.setattr(
        "app.modules.users.router.user_service.create_user",
        lambda *_: {
            "id": "u1",
            "shop_id": "s1",
            "email": "u@example.com",
            "is_active": True,
            "created_at": "2026-01-01T00:00:00Z",
        },
    )
    response = client.post(
        "/api/v1/users",
        json={"email": "u@example.com", "password": "secret123", "shop_name": "My Shop"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "u@example.com"


def test_get_me_profile(client, monkeypatch):  # noqa: ANN001
    app.dependency_overrides.clear()
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: CurrentUserSchema(
        id="u1", email="u@example.com", shop_id="s1"
    )
    monkeypatch.setattr(
        "app.modules.users.router.user_service.get_profile",
        lambda *_: {
            "user": {
                "id": "u1",
                "shop_id": "s1",
                "email": "u@example.com",
                "is_active": True,
                "created_at": "2026-01-01T00:00:00Z",
            },
            "shop": {"id": "s1", "name": "My Shop", "created_at": "2026-01-01T00:00:00Z"},
        },
    )
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["shop"]["name"] == "My Shop"
    app.dependency_overrides.clear()
