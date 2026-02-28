import pytest
from datetime import datetime

from app.core.exceptions import ValidationException
from app.modules.analytics.service import analytics_service
from app.modules.analytics.schemas import AnalyticsSnapshotCreateSchema


class StubSnapshot:
    def __init__(self, id: str = "a1", shop_id: str = "s1", snapshot_type: str = "t") -> None:
        self.id = id
        self.shop_id = shop_id
        self.snapshot_type = snapshot_type
        self.payload = {"k": "v"}
        from datetime import datetime

        self.created_at = datetime.utcnow()


def test_create_and_list_snapshots(monkeypatch) -> None:  # noqa: ANN001
    stub = StubSnapshot()
    monkeypatch.setattr("app.modules.analytics.repository.analytics_repository.create_snapshot", lambda *_: stub)
    monkeypatch.setattr("app.modules.analytics.repository.analytics_repository.list_snapshots", lambda *_: [stub])

    created = analytics_service.create_snapshot(None, "s1", AnalyticsSnapshotCreateSchema(snapshot_type="t", payload={}))
    assert created.snapshot_type == "t"

    listed = analytics_service.list_snapshots(None, "s1", None)
    assert len(listed) == 1


def test_top_products_validates_date_range(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationException):
        analytics_service.top_products(None, "s1", datetime(2026, 2, 27).date(), datetime(2026, 2, 26).date())  # type: ignore[arg-type]


def test_top_products_maps_repository_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.analytics.repository.analytics_repository.top_products",
        lambda *_args, **_kwargs: [
            {"product_id": "p1", "product_name": "Milk", "total_quantity": 3, "total_revenue": 120.0}
        ],
    )

    result = analytics_service.top_products(
        None,  # type: ignore[arg-type]
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
        5,
    )
    assert len(result) == 1
    assert result[0].product_name == "Milk"


def test_revenue_series_validation_and_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationException):
        analytics_service.revenue_series(
            None,  # type: ignore[arg-type]
            "s1",
            datetime(2026, 2, 27).date(),
            datetime(2026, 2, 26).date(),
            "day",
        )

    with pytest.raises(ValidationException):
        analytics_service.revenue_series(
            None,  # type: ignore[arg-type]
            "s1",
            datetime(2026, 2, 1).date(),
            datetime(2026, 2, 26).date(),
            "week",
        )

    monkeypatch.setattr(
        "app.modules.analytics.repository.analytics_repository.revenue_series",
        lambda *_args, **_kwargs: [{"bucket": "2026-02-26", "total_revenue": 300.0, "total_sales": 8}],
    )
    rows = analytics_service.revenue_series(
        None,  # type: ignore[arg-type]
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
        "day",
    )
    assert rows[0].total_sales == 8


def test_monthly_comparison_validation_and_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationException):
        analytics_service.monthly_comparison(None, "s1", 0)  # type: ignore[arg-type]
    with pytest.raises(ValidationException):
        analytics_service.monthly_comparison(None, "s1", 25)  # type: ignore[arg-type]

    monkeypatch.setattr(
        "app.modules.analytics.repository.analytics_repository.monthly_comparison",
        lambda *_args, **_kwargs: [{"month": "2026-02", "total_revenue": 500.0, "total_sales": 12}],
    )
    rows = analytics_service.monthly_comparison(None, "s1", 6)  # type: ignore[arg-type]
    assert rows[0].month == "2026-02"


def test_revenue_profit_summary_validation_and_computation(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationException):
        analytics_service.revenue_profit_summary(
            None,  # type: ignore[arg-type]
            "s1",
            datetime(2026, 2, 27).date(),
            datetime(2026, 2, 26).date(),
        )

    monkeypatch.setattr(
        "app.modules.analytics.repository.analytics_repository.revenue_profit_summary",
        lambda *_args, **_kwargs: {"total_revenue": 1000.0, "total_cogs": 650.0},
    )
    summary = analytics_service.revenue_profit_summary(
        None,  # type: ignore[arg-type]
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
    )
    assert summary.total_revenue == 1000.0
    assert summary.total_cogs == 650.0
    assert summary.total_profit == 350.0


def test_revenue_profit_summary_defaults_when_none_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.analytics.repository.analytics_repository.revenue_profit_summary",
        lambda *_args, **_kwargs: {"total_revenue": None, "total_cogs": None},
    )
    summary = analytics_service.revenue_profit_summary(
        None,  # type: ignore[arg-type]
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
    )
    assert summary.total_revenue == 0.0
    assert summary.total_cogs == 0.0
    assert summary.total_profit == 0.0
