import pytest
from datetime import datetime

from app.modules.analytics.schemas import AnalyticsSnapshotCreateSchema


class StubSnapshot:
    def __init__(self, id: str = "a1", shop_id: str = "s1", snapshot_type: str = "t") -> None:
        self.id = id
        self.shop_id = shop_id
        self.snapshot_type = snapshot_type
        self.payload = {"k": "v"}
        from datetime import datetime

        self.created_at = datetime.utcnow()


def test_analytics_repository_create_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.analytics.repository import analytics_repository

    class MockDB:
        def add(self, obj):
            pass

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    payload = AnalyticsSnapshotCreateSchema(snapshot_type="type", payload={"k": "v"})
    snapshot = analytics_repository.create_snapshot(MockDB(), "s1", payload)
    assert snapshot.shop_id == "s1"


def test_analytics_repository_list_snapshots(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.analytics.repository import analytics_repository

    snapshots = [StubSnapshot(snapshot_type="type1"), StubSnapshot(snapshot_type="type2")]

    class MockScalars:
        def all(self):
            return snapshots

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

    result = analytics_repository.list_snapshots(MockDB(), "s1")
    assert len(result) == 2


def test_analytics_repository_list_snapshots_by_type(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.analytics.repository import analytics_repository

    snapshots = [StubSnapshot(snapshot_type="type1")]

    class MockScalars:
        def all(self):
            return snapshots

    class MockDB:
        def scalars(self, stmt):
            return MockScalars()

    result = analytics_repository.list_snapshots(MockDB(), "s1", snapshot_type="type1")
    assert len(result) == 1


def test_analytics_repository_top_products(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.analytics.repository import analytics_repository

    class MockResult:
        def mappings(self):
            return [
                {
                    "product_id": "p1",
                    "product_name": "Milk",
                    "total_quantity": 3,
                    "total_revenue": 120.0,
                }
            ]

    class MockDB:
        def execute(self, stmt, params):
            assert "sale_items" in str(stmt)
            assert params["limit"] == 5
            return MockResult()

    rows = analytics_repository.top_products(
        MockDB(),
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
        5,
    )
    assert rows[0]["product_name"] == "Milk"


def test_analytics_repository_revenue_series_day_and_hour(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.analytics.repository import analytics_repository

    captured = []

    class MockResult:
        def mappings(self):
            return [{"bucket": "2026-02-26", "total_revenue": 100.0, "total_sales": 2}]

    class MockDB:
        def execute(self, stmt, params):
            captured.append((str(stmt), params))
            return MockResult()

    day_rows = analytics_repository.revenue_series(
        MockDB(),
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
        "day",
    )
    hour_rows = analytics_repository.revenue_series(
        MockDB(),
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
        "hour",
    )

    assert day_rows and hour_rows
    assert captured[0][1]["bucket_format"] == "YYYY-MM-DD"
    assert captured[1][1]["bucket_format"] == "YYYY-MM-DD HH24:00"


def test_analytics_repository_monthly_comparison(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.analytics.repository import analytics_repository

    class MockResult:
        def mappings(self):
            return [{"month": "2026-02", "total_revenue": 300.0, "total_sales": 6}]

    class MockDB:
        def execute(self, stmt, params):
            assert "DATE_TRUNC('month'" in str(stmt)
            assert params["months"] == 6
            return MockResult()

    rows = analytics_repository.monthly_comparison(MockDB(), "s1", 6)
    assert rows[0]["month"] == "2026-02"


def test_analytics_repository_revenue_profit_summary_with_and_without_row(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.analytics.repository import analytics_repository

    class MockMappingsWithRow:
        def first(self):
            return {"total_revenue": 250.0, "total_cogs": 175.0}

    class MockMappingsEmpty:
        def first(self):
            return None

    class MockDBWithRow:
        def execute(self, stmt, params):
            assert "avg_cost" in str(stmt)
            assert params["shop_id"] == "s1"
            class Result:
                def mappings(self_inner):
                    return MockMappingsWithRow()
            return Result()

    class MockDBEmpty:
        def execute(self, stmt, params):
            class Result:
                def mappings(self_inner):
                    return MockMappingsEmpty()
            return Result()

    with_row = analytics_repository.revenue_profit_summary(
        MockDBWithRow(),
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
    )
    empty = analytics_repository.revenue_profit_summary(
        MockDBEmpty(),
        "s1",
        datetime(2026, 2, 1).date(),
        datetime(2026, 2, 26).date(),
    )

    assert with_row["total_revenue"] == 250.0
    assert with_row["total_cogs"] == 175.0
    assert empty == {"total_revenue": 0.0, "total_cogs": 0.0}
