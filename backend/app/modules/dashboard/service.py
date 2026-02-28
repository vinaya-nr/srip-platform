from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.dashboard.schemas import DashboardSummaryResponseSchema


class DashboardService:
    def get_summary(self, db: Session, shop_id: str) -> DashboardSummaryResponseSchema:
        sales_row = db.execute(
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

        active_products_count = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM products
                    WHERE shop_id = :shop_id AND is_active = true
                    """
                ),
                {"shop_id": shop_id},
            ).scalar_one()
        )

        low_stock_count = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM (
                        SELECT p.id
                        FROM products p
                        LEFT JOIN batches b ON p.id = b.product_id AND p.shop_id = b.shop_id
                        WHERE p.shop_id = :shop_id AND p.is_active = true
                        GROUP BY p.id, p.low_stock_threshold
                        HAVING COALESCE(SUM(b.quantity), 0) <= p.low_stock_threshold
                    ) AS low_stock_products
                    """
                ),
                {"shop_id": shop_id},
            ).scalar_one()
        )

        unread_notifications_count = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM notifications
                    WHERE shop_id = :shop_id AND is_read = false
                    """
                ),
                {"shop_id": shop_id},
            ).scalar_one()
        )

        return DashboardSummaryResponseSchema(
            today_sales_total=int(sales_row["total_sales"]) if sales_row else 0,
            today_revenue_total=Decimal(str(sales_row["total_revenue"])) if sales_row else Decimal("0"),
            active_products_count=active_products_count,
            low_stock_count=low_stock_count,
            unread_notifications_count=unread_notifications_count,
        )


dashboard_service = DashboardService()
