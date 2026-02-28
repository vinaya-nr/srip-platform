import logging
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import text

from app.core.database import SessionLocal
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
LOW_STOCK_ALERT_COOLDOWN_HOURS = 12
EXPIRY_ALERT_COOLDOWN_HOURS = 12


@celery_app.task(name="app.workers.tasks.stock_alerts.check_low_stock")
def check_low_stock(shop_id: str | None = None) -> int:
    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT p.shop_id, p.id AS product_id, p.name, p.low_stock_threshold,
                       p.sku,
                       COALESCE(SUM(b.quantity), 0) AS stock
                FROM products p
                LEFT JOIN batches b ON p.id = b.product_id AND p.shop_id = b.shop_id
                WHERE (:shop_id IS NULL OR p.shop_id = :shop_id)
                  AND p.is_active = true
                GROUP BY p.shop_id, p.id, p.name, p.low_stock_threshold
                HAVING COALESCE(SUM(b.quantity), 0) <= p.low_stock_threshold
                """
            ),
            {"shop_id": shop_id},
        ).mappings().all()
        created = 0
        for row in rows:
            product_label = f"{row['name']} ({row['sku']})" if row.get("sku") else row["name"]
            recent_alert = db.execute(
                text(
                    """
                    SELECT id
                    FROM notifications
                    WHERE shop_id = :shop_id
                      AND event_type = 'low_stock_detected'
                      AND message LIKE :message_prefix
                      AND created_at >= now() - (:cooldown_hours * interval '1 hour')
                    LIMIT 1
                    """
                ),
                {
                    "shop_id": row["shop_id"],
                    "message_prefix": f"{product_label} stock is %",
                    "cooldown_hours": LOW_STOCK_ALERT_COOLDOWN_HOURS,
                },
            ).first()
            if recent_alert:
                continue

            db.execute(
                text(
                    """
                    INSERT INTO notifications (id, shop_id, event_type, title, message, is_read, created_at)
                    VALUES (:id, :shop_id, :event_type, :title, :message, false, now())
                    """
                ),
                    {
                        "id": str(uuid4()),
                        "shop_id": row["shop_id"],
                        "event_type": "low_stock_detected",
                        "title": "Low Stock Alert",
                        "message": f"{product_label} stock is {row['stock']} (threshold {row['low_stock_threshold']}).",
                    },
                )
            created += 1
        db.commit()
    logger.info("low_stock_check_completed", extra={"extra": {"alerts_created": created}})
    return created


@celery_app.task(name="app.workers.tasks.stock_alerts.check_expiry_dates")
def check_expiry_dates(within_days: int = 15) -> int:
    cutoff = date.today() + timedelta(days=within_days)
    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT b.shop_id, b.product_id, b.expiry_date, p.name, p.sku
                FROM batches b
                JOIN products p ON p.id = b.product_id AND p.shop_id = b.shop_id
                WHERE b.expiry_date IS NOT NULL
                  AND b.expiry_date <= :cutoff
                  AND b.quantity > 0
                  AND p.is_active = true
                """
            ),
            {"cutoff": cutoff},
        ).mappings().all()
        created = 0
        for row in rows:
            product_label = f"{row['name']} ({row['sku']})" if row.get("sku") else row["name"]
            recent_alert = db.execute(
                text(
                    """
                    SELECT id
                    FROM notifications
                    WHERE shop_id = :shop_id
                      AND event_type = 'expiry_alert'
                      AND message LIKE :message_prefix
                      AND created_at >= now() - (:cooldown_hours * interval '1 hour')
                    LIMIT 1
                    """
                ),
                {
                    "shop_id": row["shop_id"],
                    "message_prefix": f"{product_label} batch expires on {row['expiry_date']}%",
                    "cooldown_hours": EXPIRY_ALERT_COOLDOWN_HOURS,
                },
            ).first()
            if recent_alert:
                continue

            db.execute(
                text(
                    """
                    INSERT INTO notifications (id, shop_id, event_type, title, message, is_read, created_at)
                    VALUES (:id, :shop_id, :event_type, :title, :message, false, now())
                    """
                ),
                    {
                        "id": str(uuid4()),
                        "shop_id": row["shop_id"],
                        "event_type": "expiry_alert",
                        "title": "Batch Expiry Alert",
                        "message": f"{product_label} batch expires on {row['expiry_date']}.",
                    },
                )
            created += 1
        db.commit()
    logger.info("expiry_check_completed", extra={"extra": {"alerts_created": created}})
    return created
