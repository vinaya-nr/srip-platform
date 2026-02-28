from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUserSchema
from app.modules.dashboard.schemas import DashboardSummaryResponseSchema
from app.modules.dashboard.service import dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponseSchema)
def get_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> DashboardSummaryResponseSchema:
    return dashboard_service.get_summary(db, current_user.shop_id)
