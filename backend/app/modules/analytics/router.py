from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.analytics.schemas import (
    AnalyticsSnapshotCreateSchema,
    AnalyticsSnapshotResponseSchema,
    MonthlyComparisonPointSchema,
    RevenueProfitSummarySchema,
    RevenueSeriesPointSchema,
    TopProductPointSchema,
)
from app.modules.analytics.service import analytics_service
from app.modules.auth.schemas import CurrentUserSchema

router = APIRouter()


@router.post("/snapshots", response_model=AnalyticsSnapshotResponseSchema, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    payload: AnalyticsSnapshotCreateSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> AnalyticsSnapshotResponseSchema:
    return analytics_service.create_snapshot(db, current_user.shop_id, payload)


@router.get("/snapshots", response_model=list[AnalyticsSnapshotResponseSchema])
def list_snapshots(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    snapshot_type: str | None = None,
) -> list[AnalyticsSnapshotResponseSchema]:
    return analytics_service.list_snapshots(db, current_user.shop_id, snapshot_type)


@router.get("/top-products", response_model=list[TopProductPointSchema])
def top_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    from_date: date = Query(default_factory=date.today),
    to_date: date = Query(default_factory=date.today),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[TopProductPointSchema]:
    return analytics_service.top_products(db, current_user.shop_id, from_date, to_date, limit)


@router.get("/revenue-series", response_model=list[RevenueSeriesPointSchema])
def revenue_series(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=6)),
    to_date: date = Query(default_factory=date.today),
    bucket: str = Query(default="day"),
) -> list[RevenueSeriesPointSchema]:
    return analytics_service.revenue_series(db, current_user.shop_id, from_date, to_date, bucket)


@router.get("/monthly-comparison", response_model=list[MonthlyComparisonPointSchema])
def monthly_comparison(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    months: int = Query(default=6, ge=1, le=24),
) -> list[MonthlyComparisonPointSchema]:
    return analytics_service.monthly_comparison(db, current_user.shop_id, months)


@router.get("/revenue-profit-summary", response_model=RevenueProfitSummarySchema)
def revenue_profit_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=6)),
    to_date: date = Query(default_factory=date.today),
) -> RevenueProfitSummarySchema:
    return analytics_service.revenue_profit_summary(db, current_user.shop_id, from_date, to_date)
