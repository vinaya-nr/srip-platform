from celery.schedules import crontab


def get_beat_schedule() -> dict:
    return {
        "check-low-stock-every-30-minutes": {
            "task": "app.workers.tasks.stock_alerts.check_low_stock",
            "schedule": crontab(minute="*/30"),
        },
        "check-expiry-daily": {
            "task": "app.workers.tasks.stock_alerts.check_expiry_dates",
            "schedule": crontab(minute=0, hour=2),
        },
        "monthly-summary": {
            "task": "app.workers.tasks.reports.monthly_summary",
            "schedule": crontab(minute=0, hour=3, day_of_month=1),
        },
        "nightly-snapshot": {
            "task": "app.workers.tasks.analytics.nightly_snapshot",
            "schedule": crontab(minute=0, hour=1),
        },
    }
