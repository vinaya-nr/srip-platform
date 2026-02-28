import json
import logging
from datetime import date
from uuid import uuid4

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_redis_client
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
redis_client = get_redis_client()


@celery_app.task(name="app.workers.tasks.analytics.ingest_sale_event")
def ingest_sale_event(sale_id: str, shop_id: str, correlation_id: str) -> dict:
    with SessionLocal() as db:
        sale_row = db.execute(
            text(
                """
                SELECT id, shop_id, sale_number, total_amount, created_at
                FROM sales
                WHERE id = :sale_id AND shop_id = :shop_id
                """
            ),
            {"sale_id": sale_id, "shop_id": shop_id},
        ).mappings().first()

        items = db.execute(
            text(
                """
                SELECT product_id, quantity, unit_price, line_total
                FROM sale_items
                WHERE sale_id = :sale_id
                """
            ),
            {"sale_id": sale_id},
        ).mappings().all()

        event = {
            "event_type": "sale_ingested",
            "sale_id": str(sale_id),
            "shop_id": str(shop_id),
            "sale_number": sale_row["sale_number"] if sale_row else "",
            "total_amount": float(sale_row["total_amount"]) if sale_row else 0.0,
            "items": [
                {
                    "product_id": str(item["product_id"]),
                    "quantity": int(item["quantity"]),
                    "unit_price": float(item["unit_price"]),
                    "line_total": float(item["line_total"]),
                }
                for item in items
            ],
            "correlation_id": str(correlation_id),
        }
        redis_client.xadd("srip:sales:events", {"data": json.dumps(event)}, maxlen=settings.redis_stream_maxlen)

        db.execute(
            text(
                """
                INSERT INTO analytics_snapshots (id, shop_id, snapshot_type, payload, created_at)
                VALUES (:id, :shop_id, :snapshot_type, CAST(:payload AS jsonb), now())
                """
            ),
            {
                "id": str(uuid4()),
                "shop_id": shop_id,
                "snapshot_type": "sale_event",
                "payload": json.dumps(event),
            },
        )
        db.commit()
    logger.info("sale_event_ingested", extra={"shop_id": shop_id, "extra": {"sale_id": sale_id}})
    return event


@celery_app.task(name="app.workers.tasks.analytics.stream_inventory_event")
def stream_inventory_event(
    shop_id: str,
    product_id: str,
    movement_type: str,
    quantity: int,
    correlation_id: str,
) -> dict:
    event = {
        "event_type": "inventory_stream",
        "shop_id": shop_id,
        "product_id": product_id,
        "movement_type": movement_type,
        "quantity": quantity,
        "correlation_id": correlation_id,
    }
    redis_client.xadd("srip:inventory:events", {"data": json.dumps(event)}, maxlen=settings.redis_stream_maxlen)
    logger.info("inventory_event_streamed", extra={"shop_id": shop_id, "extra": event})
    return event


@celery_app.task(name="app.workers.tasks.analytics.compute_slow_movers")
def compute_slow_movers(shop_id: str | None = None) -> int:
    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT p.shop_id, p.id AS product_id, p.name, COALESCE(SUM(si.quantity), 0) AS sold_qty
                FROM products p
                LEFT JOIN sale_items si ON si.product_id = p.id
                LEFT JOIN sales s ON s.id = si.sale_id AND s.shop_id = p.shop_id
                WHERE (:shop_id IS NULL OR p.shop_id = :shop_id)
                GROUP BY p.shop_id, p.id, p.name
                HAVING COALESCE(SUM(si.quantity), 0) < 5
                """
            ),
            {"shop_id": shop_id},
        ).mappings().all()
    logger.info("slow_movers_computed", extra={"extra": {"count": len(rows)}})
    return len(rows)


@celery_app.task(name="app.workers.tasks.analytics.nightly_snapshot")
def nightly_snapshot() -> int:
    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT shop_id, COUNT(*) AS total_sales, COALESCE(SUM(total_amount), 0) AS total_revenue
                FROM sales
                WHERE DATE(created_at) = :today
                GROUP BY shop_id
                """
            ),
            {"today": date.today()},
        ).mappings().all()
        for row in rows:
            payload = {
                "date": str(date.today()),
                "total_sales": int(row["total_sales"]),
                "total_revenue": float(row["total_revenue"]),
            }
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
                    "snapshot_type": "nightly_snapshot",
                    "payload": json.dumps(payload),
                },
            )
        db.commit()
    logger.info("nightly_snapshot_completed", extra={"extra": {"rows_written": len(rows)}})
    return len(rows)
