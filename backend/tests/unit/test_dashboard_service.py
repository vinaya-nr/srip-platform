from decimal import Decimal

from app.modules.dashboard.service import dashboard_service


def test_dashboard_summary_with_data() -> None:
    class SalesResult:
        def mappings(self):
            class M:
                def first(self_inner):
                    return {"total_sales": 3, "total_revenue": Decimal("145.00")}

            return M()

    class ScalarResult:
        def __init__(self, value: int):
            self._value = value

        def scalar_one(self):
            return self._value

    class MockDB:
        def __init__(self):
            self.calls = 0

        def execute(self, _stmt, _params):
            self.calls += 1
            if self.calls == 1:
                return SalesResult()
            if self.calls == 2:
                return ScalarResult(8)
            if self.calls == 3:
                return ScalarResult(2)
            return ScalarResult(5)

    summary = dashboard_service.get_summary(MockDB(), "shop-1")
    assert summary.today_sales_total == 3
    assert summary.today_revenue_total == Decimal("145.00")
    assert summary.active_products_count == 8
    assert summary.low_stock_count == 2
    assert summary.unread_notifications_count == 5


def test_dashboard_summary_without_sales_row() -> None:
    class SalesResult:
        def mappings(self):
            class M:
                def first(self_inner):
                    return None

            return M()

    class ScalarResult:
        def __init__(self, value: int):
            self._value = value

        def scalar_one(self):
            return self._value

    class MockDB:
        def __init__(self):
            self.calls = 0

        def execute(self, _stmt, _params):
            self.calls += 1
            if self.calls == 1:
                return SalesResult()
            if self.calls == 2:
                return ScalarResult(0)
            if self.calls == 3:
                return ScalarResult(0)
            return ScalarResult(0)

    summary = dashboard_service.get_summary(MockDB(), "shop-1")
    assert summary.today_sales_total == 0
    assert summary.today_revenue_total == Decimal("0")
    assert summary.active_products_count == 0
    assert summary.low_stock_count == 0
    assert summary.unread_notifications_count == 0

