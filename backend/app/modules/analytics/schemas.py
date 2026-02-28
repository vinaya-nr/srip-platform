from datetime import datetime

from pydantic import BaseModel


class AnalyticsSnapshotCreateSchema(BaseModel):
    snapshot_type: str
    payload: dict


class AnalyticsSnapshotResponseSchema(BaseModel):
    id: str
    shop_id: str
    snapshot_type: str
    payload: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class TopProductPointSchema(BaseModel):
    product_id: str
    product_name: str
    total_quantity: int
    total_revenue: float


class RevenueSeriesPointSchema(BaseModel):
    bucket: str
    total_revenue: float
    total_sales: int


class MonthlyComparisonPointSchema(BaseModel):
    month: str
    total_revenue: float
    total_sales: int


class RevenueProfitSummarySchema(BaseModel):
    total_revenue: float
    total_profit: float
    total_cogs: float
