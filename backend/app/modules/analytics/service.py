from datetime import date

from app.core.exceptions import ValidationException
from sqlalchemy.orm import Session

from app.modules.analytics.repository import analytics_repository
from app.modules.analytics.schemas import (
    AnalyticsSnapshotCreateSchema,
    AnalyticsSnapshotResponseSchema,
    MonthlyComparisonPointSchema,
    RevenueProfitSummarySchema,
    RevenueSeriesPointSchema,
    TopProductPointSchema,
)


class AnalyticsService:
    def create_snapshot(
        self,
        db: Session,
        shop_id: str,
        payload: AnalyticsSnapshotCreateSchema,
    ) -> AnalyticsSnapshotResponseSchema:
        snapshot = analytics_repository.create_snapshot(db, shop_id, payload)
        return AnalyticsSnapshotResponseSchema.model_validate(snapshot)

    def list_snapshots(
        self,
        db: Session,
        shop_id: str,
        snapshot_type: str | None = None,
    ) -> list[AnalyticsSnapshotResponseSchema]:
        snapshots = analytics_repository.list_snapshots(db, shop_id, snapshot_type)
        return [AnalyticsSnapshotResponseSchema.model_validate(s) for s in snapshots]

    def top_products(
        self,
        db: Session,
        shop_id: str,
        from_date: date,
        to_date: date,
        limit: int = 5,
    ) -> list[TopProductPointSchema]:
        if from_date > to_date:
            raise ValidationException("from_date cannot be greater than to_date.")
        rows = analytics_repository.top_products(db, shop_id, from_date, to_date, limit)
        return [TopProductPointSchema.model_validate(row) for row in rows]

    def revenue_series(
        self,
        db: Session,
        shop_id: str,
        from_date: date,
        to_date: date,
        bucket: str = "day",
    ) -> list[RevenueSeriesPointSchema]:
        if from_date > to_date:
            raise ValidationException("from_date cannot be greater than to_date.")
        if bucket not in {"day", "hour"}:
            raise ValidationException("bucket must be either 'day' or 'hour'.")
        rows = analytics_repository.revenue_series(db, shop_id, from_date, to_date, bucket)
        return [RevenueSeriesPointSchema.model_validate(row) for row in rows]

    def monthly_comparison(
        self,
        db: Session,
        shop_id: str,
        months: int = 6,
    ) -> list[MonthlyComparisonPointSchema]:
        if months < 1 or months > 24:
            raise ValidationException("months must be between 1 and 24.")
        rows = analytics_repository.monthly_comparison(db, shop_id, months)
        return [MonthlyComparisonPointSchema.model_validate(row) for row in rows]

    def revenue_profit_summary(
        self,
        db: Session,
        shop_id: str,
        from_date: date,
        to_date: date,
    ) -> RevenueProfitSummarySchema:
        if from_date > to_date:
            raise ValidationException("from_date cannot be greater than to_date.")
        row = analytics_repository.revenue_profit_summary(db, shop_id, from_date, to_date)
        total_revenue = float(row.get("total_revenue", 0) or 0)
        total_cogs = float(row.get("total_cogs", 0) or 0)
        total_profit = total_revenue - total_cogs
        return RevenueProfitSummarySchema(
            total_revenue=total_revenue,
            total_profit=total_profit,
            total_cogs=total_cogs,
        )


analytics_service = AnalyticsService()
