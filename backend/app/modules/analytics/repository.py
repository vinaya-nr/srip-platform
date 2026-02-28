from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.analytics.models import AnalyticsSnapshot
from app.modules.analytics.schemas import AnalyticsSnapshotCreateSchema


class AnalyticsRepository:
    def create_snapshot(
        self,
        db: Session,
        shop_id: str,
        payload: AnalyticsSnapshotCreateSchema,
    ) -> AnalyticsSnapshot:
        snapshot = AnalyticsSnapshot(shop_id=shop_id, **payload.model_dump())
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    def list_snapshots(self, db: Session, shop_id: str, snapshot_type: str | None = None) -> list[AnalyticsSnapshot]:
        stmt = select(AnalyticsSnapshot).where(AnalyticsSnapshot.shop_id == shop_id)
        if snapshot_type:
            stmt = stmt.where(AnalyticsSnapshot.snapshot_type == snapshot_type)
        stmt = stmt.order_by(AnalyticsSnapshot.created_at.desc())
        return list(db.scalars(stmt).all())

    def top_products(
        self,
        db: Session,
        shop_id: str,
        from_date: date,
        to_date: date,
        limit: int = 5,
    ) -> list[dict]:
        rows = db.execute(
            text(
                """
                SELECT
                    CAST(si.product_id AS text) AS product_id,
                    p.name AS product_name,
                    SUM(si.quantity)::int AS total_quantity,
                    COALESCE(SUM(si.line_total), 0)::float AS total_revenue
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                JOIN products p ON p.id = si.product_id AND p.shop_id = s.shop_id
                WHERE s.shop_id = :shop_id
                  AND DATE(s.created_at) BETWEEN :from_date AND :to_date
                GROUP BY si.product_id, p.name
                ORDER BY total_quantity DESC, total_revenue DESC
                LIMIT :limit
                """
            ),
            {
                "shop_id": shop_id,
                "from_date": from_date,
                "to_date": to_date,
                "limit": limit,
            },
        ).mappings()
        return [dict(row) for row in rows]

    def revenue_series(
        self,
        db: Session,
        shop_id: str,
        from_date: date,
        to_date: date,
        bucket: str,
    ) -> list[dict]:
        sql_bucket = "hour" if bucket == "hour" else "day"
        rows = db.execute(
            text(
                f"""
                SELECT
                    TO_CHAR(DATE_TRUNC('{sql_bucket}', s.created_at), :bucket_format) AS bucket,
                    COALESCE(SUM(s.total_amount), 0)::float AS total_revenue,
                    COUNT(*)::int AS total_sales
                FROM sales s
                WHERE s.shop_id = :shop_id
                  AND DATE(s.created_at) BETWEEN :from_date AND :to_date
                GROUP BY DATE_TRUNC('{sql_bucket}', s.created_at)
                ORDER BY DATE_TRUNC('{sql_bucket}', s.created_at) ASC
                """
            ),
            {
                "shop_id": shop_id,
                "from_date": from_date,
                "to_date": to_date,
                "bucket_format": "YYYY-MM-DD HH24:00" if sql_bucket == "hour" else "YYYY-MM-DD",
            },
        ).mappings()
        return [dict(row) for row in rows]

    def monthly_comparison(self, db: Session, shop_id: str, months: int = 6) -> list[dict]:
        rows = db.execute(
            text(
                """
                SELECT
                    TO_CHAR(DATE_TRUNC('month', s.created_at), 'YYYY-MM') AS month,
                    COALESCE(SUM(s.total_amount), 0)::float AS total_revenue,
                    COUNT(*)::int AS total_sales
                FROM sales s
                WHERE s.shop_id = :shop_id
                  AND s.created_at >= DATE_TRUNC('month', CURRENT_DATE) - (:months - 1) * INTERVAL '1 month'
                GROUP BY DATE_TRUNC('month', s.created_at)
                ORDER BY DATE_TRUNC('month', s.created_at) ASC
                """
            ),
            {"shop_id": shop_id, "months": months},
        ).mappings()
        return [dict(row) for row in rows]

    def revenue_profit_summary(
        self,
        db: Session,
        shop_id: str,
        from_date: date,
        to_date: date,
    ) -> dict:
        row = db.execute(
            text(
                """
                WITH avg_cost AS (
                    SELECT
                        b.product_id,
                        COALESCE(AVG(b.unit_cost), 0)::float AS avg_unit_cost
                    FROM batches b
                    WHERE b.shop_id = :shop_id
                    GROUP BY b.product_id
                )
                SELECT
                    COALESCE(SUM(si.line_total), 0)::float AS total_revenue,
                    COALESCE(SUM(si.quantity * COALESCE(ac.avg_unit_cost, 0)), 0)::float AS total_cogs
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                LEFT JOIN avg_cost ac ON ac.product_id = si.product_id
                WHERE s.shop_id = :shop_id
                  AND DATE(s.created_at) BETWEEN :from_date AND :to_date
                """
            ),
            {
                "shop_id": shop_id,
                "from_date": from_date,
                "to_date": to_date,
            },
        ).mappings().first()
        return dict(row) if row else {"total_revenue": 0.0, "total_cogs": 0.0}


analytics_repository = AnalyticsRepository()
