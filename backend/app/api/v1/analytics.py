from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.core.security import require_roles
from backend.app.models.models import User
from backend.app.models.enums import UserRole
from backend.app.schemas.analytics import AnalyticsOverviewResponse, AnalyticsTrendsResponse
from backend.app.schemas.common import StandardResponse
from backend.app.repositories.analytics_repo import AnalyticsRepository

router = APIRouter(prefix="/analytics", tags=["Analytics & AI Performance"])

@router.get("/overview", response_model=StandardResponse[AnalyticsOverviewResponse])
async def get_overview_analytics(
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = AnalyticsRepository(db)
    data = await repo.get_overview(current_user.organization_id)
    return StandardResponse(data=AnalyticsOverviewResponse(**data))

@router.get("/trends", response_model=StandardResponse[AnalyticsTrendsResponse])
async def get_trends_analytics(
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = AnalyticsRepository(db)
    data = await repo.get_trends(current_user.organization_id)
    return StandardResponse(data=AnalyticsTrendsResponse(**data))
