from celery import Celery

from app.core.config import settings
from app.workers.schedules import get_beat_schedule

celery_app = Celery(
    "srip",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.stock_alerts",
        "app.workers.tasks.reports",
        "app.workers.tasks.analytics",
    ],
)

celery_app.conf.update(
    timezone="UTC",
    task_track_started=True,
    result_expires=3600,
    beat_schedule=get_beat_schedule(),
)
