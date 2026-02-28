from app.main import app
from app.modules.auth.schemas import CurrentUserSchema

from ..test_conf import client


def test_list_products(client, monkeypatch):  # noqa: ANN001
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: CurrentUserSchema(
        id="u1", email="u@example.com", shop_id="s1"
    )
    monkeypatch.setattr(
        "app.modules.products.router.product_service.list_products",
        lambda *_args, **_kwargs: {
            "items": [
                {
                    "id": "p1",
                    "shop_id": "s1",
                    "category_id": None,
                    "name": "Pen",
                    "sku": "PEN-1",
                    "description": None,
                    "price": "10.00",
                    "low_stock_threshold": 5,
                    "is_active": True,
                }
            ],
            "total": 1,
            "skip": 0,
            "limit": 20,
        },
    )
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert response.json()["items"][0]["sku"] == "PEN-1"
    app.dependency_overrides.clear()
