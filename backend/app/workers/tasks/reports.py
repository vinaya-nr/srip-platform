import logging
from datetime import date
from uuid import uuid4

from sqlalchemy import text

from app.core.database import SessionLocal
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.reports.generate_daily_report")
def generate_daily_report(shop_id: str) -> dict:
    with SessionLocal() as db:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS total_sales,
                       COALESCE(SUM(total_amount), 0) AS total_revenue
                FROM sales
                WHERE shop_id = :shop_id AND DATE(created_at) = :today
                """
            ),
            {"shop_id": shop_id, "today": date.today()},
        ).mappings().first()
    payload = {
        "shop_id": shop_id,
        "date": str(date.today()),
        "total_sales": int(row["total_sales"]) if row else 0,
        "total_revenue": float(row["total_revenue"]) if row else 0.0,
    }
    logger.info("daily_report_generated", extra={"shop_id": shop_id, "extra": payload})
    return payload


@celery_app.task(name="app.workers.tasks.reports.monthly_summary")
def monthly_summary() -> int:
    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT shop_id,
                       DATE_TRUNC('month', created_at) AS month_bucket,
                       COUNT(*) AS total_sales,
                       COALESCE(SUM(total_amount), 0) AS total_revenue
                FROM sales
                GROUP BY shop_id, DATE_TRUNC('month', created_at)
                """
            )
        ).mappings().all()

        for row in rows:
            db.execute(
                text(
                    """
                    INSERT INTO analytics_snapshots (id, shop_id, snapshot_type, payload, created_at)
                    VALUES (:id, :shop_id, :snapshot_type, CAST(:payload AS jsonb), now())
                    """
                ),
                {
                    "id": str(uuid4()),
                    "shop_id": row["shop_id"],
                    "snapshot_type": "monthly_summary",
                    "payload": (
                        f'{{"month":"{row["month_bucket"]}","total_sales":{int(row["total_sales"])},'
                        f'"total_revenue":{float(row["total_revenue"])}}}'
                    ),
                },
            )
        db.commit()
    logger.info("monthly_summary_completed", extra={"extra": {"rows_written": len(rows)}})
    return len(rows)
