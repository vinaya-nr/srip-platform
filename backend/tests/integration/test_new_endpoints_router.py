from app.main import app
from app.modules.auth.schemas import CurrentUserSchema

from ..test_conf import client


def _override_user() -> None:
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: CurrentUserSchema(
        id="u1",
        email="u@example.com",
        shop_id="s1",
    )


def test_get_sale_by_id(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.sales.router.sales_service.get_sale",
        lambda *_args, **_kwargs: {
            "id": "sale-1",
            "shop_id": "s1",
            "sale_number": "SRIP-20260224-ABC12345",
            "total_amount": "100.00",
            "created_at": "2026-02-24T10:00:00Z",
            "items": [{"product_id": "p1", "quantity": 2, "unit_price": "50.00", "line_total": "100.00"}],
        },
    )
    response = client.get("/api/v1/sales/sale-1")
    assert response.status_code == 200
    assert response.json()["sale_number"] == "SRIP-20260224-ABC12345"
    app.dependency_overrides.clear()


def test_get_sale_not_found_router(client, monkeypatch):  # noqa: ANN001
    _override_user()
    from app.core.exceptions import NotFoundException
    monkeypatch.setattr(
        "app.modules.sales.router.sales_service.get_sale",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(NotFoundException("missing")),
    )
    response = client.get("/api/v1/sales/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    app.dependency_overrides.clear()


def test_create_sale_validation_error(client, monkeypatch):  # noqa: ANN001
    _override_user()
    from app.core.exceptions import ValidationException
    monkeypatch.setattr(
        "app.modules.sales.router.sales_service.create_sale",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValidationException("bad")),
    )
    response = client.post("/api/v1/sales", json={})
    assert response.status_code == 422 or response.status_code == 400
    app.dependency_overrides.clear()


def test_list_sales_with_date_filters(client, monkeypatch):  # noqa: ANN001
    _override_user()
    captured = {}

    def fake_list_sales(_db, _shop_id, skip, limit, from_date, to_date):
        captured["skip"] = skip
        captured["limit"] = limit
        captured["from_date"] = str(from_date)
        captured["to_date"] = str(to_date)
        return {
            "items": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
        }

    monkeypatch.setattr("app.modules.sales.router.sales_service.list_sales", fake_list_sales)
    response = client.get("/api/v1/sales?skip=0&limit=20&from_date=2026-02-01&to_date=2026-02-28")
    assert response.status_code == 200
    assert captured == {
        "skip": 0,
        "limit": 20,
        "from_date": "2026-02-01",
        "to_date": "2026-02-28",
    }
    app.dependency_overrides.clear()


def test_list_sales_validation_error_router(client, monkeypatch):  # noqa: ANN001
    _override_user()
    from app.core.exceptions import ValidationException

    monkeypatch.setattr(
        "app.modules.sales.router.sales_service.list_sales",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValidationException("From date cannot be after To date.")),
    )
    response = client.get("/api/v1/sales?from_date=2026-03-01&to_date=2026-02-01")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    app.dependency_overrides.clear()


def test_get_product_stock(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.products.router.product_service.get_product_stock",
        lambda *_args, **_kwargs: {"product_id": "p1", "shop_id": "s1", "current_stock": 123},
    )
    response = client.get("/api/v1/products/p1/stock")
    assert response.status_code == 200
    assert response.json()["current_stock"] == 123
    app.dependency_overrides.clear()


def test_get_dashboard_summary(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.dashboard.router.dashboard_service.get_summary",
        lambda *_args, **_kwargs: {
            "today_sales_total": 5,
            "today_revenue_total": "450.50",
            "active_products_count": 40,
            "low_stock_count": 3,
            "unread_notifications_count": 2,
        },
    )
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    assert response.json()["low_stock_count"] == 3
    app.dependency_overrides.clear()


def test_analytics_list_snapshots(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.analytics.router.analytics_service.list_snapshots",
        lambda *_args, **_kwargs: [
            {
                "id": "a1",
                "shop_id": "s1",
                "snapshot_type": "sale_event",
                "payload": {"sale_id": "sale-1"},
                "created_at": "2026-02-26T10:00:00Z",
            }
        ],
    )
    response = client.get("/api/v1/analytics/snapshots?snapshot_type=sale_event")
    assert response.status_code == 200
    assert response.json()[0]["snapshot_type"] == "sale_event"
    app.dependency_overrides.clear()


def test_analytics_top_products(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.analytics.router.analytics_service.top_products",
        lambda *_args, **_kwargs: [
            {
                "product_id": "p1",
                "product_name": "Milk",
                "total_quantity": 12,
                "total_revenue": 480.0,
            }
        ],
    )
    response = client.get("/api/v1/analytics/top-products?from_date=2026-02-01&to_date=2026-02-28&limit=5")
    assert response.status_code == 200
    assert response.json()[0]["product_name"] == "Milk"
    app.dependency_overrides.clear()


def test_analytics_revenue_series(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.analytics.router.analytics_service.revenue_series",
        lambda *_args, **_kwargs: [
            {"bucket": "2026-02-26", "total_revenue": 145.0, "total_sales": 3},
        ],
    )
    response = client.get("/api/v1/analytics/revenue-series?from_date=2026-02-20&to_date=2026-02-26&bucket=day")
    assert response.status_code == 200
    assert response.json()[0]["total_sales"] == 3
    app.dependency_overrides.clear()


def test_analytics_monthly_comparison(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.analytics.router.analytics_service.monthly_comparison",
        lambda *_args, **_kwargs: [
            {"month": "2026-02", "total_revenue": 145.0, "total_sales": 3},
        ],
    )
    response = client.get("/api/v1/analytics/monthly-comparison?months=6")
    assert response.status_code == 200
    assert response.json()[0]["month"] == "2026-02"
    app.dependency_overrides.clear()


def test_analytics_revenue_profit_summary(client, monkeypatch):  # noqa: ANN001
    _override_user()
    monkeypatch.setattr(
        "app.modules.analytics.router.analytics_service.revenue_profit_summary",
        lambda *_args, **_kwargs: {
            "total_revenue": 145.0,
            "total_profit": 40.0,
            "total_cogs": 105.0,
        },
    )
    response = client.get("/api/v1/analytics/revenue-profit-summary?from_date=2026-02-20&to_date=2026-02-26")
    assert response.status_code == 200
    assert response.json()["total_profit"] == 40.0
    app.dependency_overrides.clear()
