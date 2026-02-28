from app.main import app
from app.modules.auth.schemas import CurrentUserSchema

from ..test_conf import client


def test_list_categories(client, monkeypatch):  # noqa: ANN001
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: CurrentUserSchema(
        id="u1", email="u@example.com", shop_id="s1"
    )
    monkeypatch.setattr(
        "app.modules.categories.router.category_service.list_categories",
        lambda *_args, **_kwargs: [
            {
                "id": "cat-1",
                "shop_id": "s1",
                "name": "Groceries",
                "created_at": "2026-02-20T00:00:00",
            }
        ],
    )
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Groceries"
    app.dependency_overrides.clear()


def test_create_category(client, monkeypatch):  # noqa: ANN001
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: CurrentUserSchema(
        id="u1", email="u@example.com", shop_id="s1"
    )
    monkeypatch.setattr(
        "app.modules.categories.router.category_service.create_category",
        lambda *_args, **_kwargs: {
            "id": "cat-1",
            "shop_id": "s1",
            "name": "Snacks",
            "created_at": "2026-02-20T00:00:00",
        },
    )
    response = client.post("/api/v1/categories", json={"name": "Snacks"})
    assert response.status_code == 201
    assert response.json()["name"] == "Snacks"
    app.dependency_overrides.clear()
