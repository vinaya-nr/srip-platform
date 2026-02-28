from decimal import Decimal

from pydantic import BaseModel


class DashboardSummaryResponseSchema(BaseModel):
    today_sales_total: int
    today_revenue_total: Decimal
    active_products_count: int
    low_stock_count: int
    unread_notifications_count: int
