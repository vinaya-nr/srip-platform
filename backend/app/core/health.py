from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import get_redis_client
from app.workers.celery_app import celery_app


def check_postgres(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception:
        return False


def check_celery() -> bool:
    try:
        inspect = celery_app.control.inspect(timeout=1.0)
        ping = inspect.ping()
        return bool(ping)
    except Exception:
        return False
