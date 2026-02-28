from typing import Annotated

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.health import check_celery, check_postgres, check_redis
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.inventory.router import router as inventory_router
from app.modules.notifications.router import router as notifications_router
from app.modules.products.router import router as products_router
from app.modules.sales.router import router as sales_router
from app.modules.users.router import router as users_router


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(MetricsMiddleware)

    register_exception_handlers(app)

    @app.get(f"{settings.api_v1_prefix}/health", tags=["health"])
    def healthcheck(db: Annotated[Session, Depends(get_db)]) -> dict:
        postgres_ok = check_postgres(db)
        redis_ok = check_redis()
        celery_ok = check_celery()
        all_ok = postgres_ok and redis_ok and celery_ok
        return {
            "ok": all_ok,
            "status": "healthy" if all_ok else "degraded",
            "components": {
                "postgres": postgres_ok,
                "redis": redis_ok,
                "celery": celery_ok,
            },
        }

    @app.get("/metrics", tags=["observability"])
    def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
    app.include_router(users_router, prefix=f"{settings.api_v1_prefix}/users", tags=["users"])
    app.include_router(categories_router, prefix=f"{settings.api_v1_prefix}/categories", tags=["categories"])
    app.include_router(products_router, prefix=f"{settings.api_v1_prefix}/products", tags=["products"])
    app.include_router(inventory_router, prefix=f"{settings.api_v1_prefix}/inventory", tags=["inventory"])
    app.include_router(sales_router, prefix=f"{settings.api_v1_prefix}/sales", tags=["sales"])
    app.include_router(dashboard_router, prefix=f"{settings.api_v1_prefix}/dashboard", tags=["dashboard"])
    app.include_router(analytics_router, prefix=f"{settings.api_v1_prefix}/analytics", tags=["analytics"])
    app.include_router(
        notifications_router,
        prefix=f"{settings.api_v1_prefix}/notifications",
        tags=["notifications"],
    )

    return app


app = create_app()
