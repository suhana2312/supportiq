from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.core.security import get_current_user, require_roles
from backend.app.core.exceptions import NotFoundError
from backend.app.models.models import User, Organization
from backend.app.models.enums import UserRole
from backend.app.schemas.organization import OrganizationResponse, OrganizationUpdateRequest
from backend.app.schemas.common import StandardResponse
from backend.app.repositories.organization_repo import OrganizationRepository

router = APIRouter(prefix="/organization", tags=["Organization & AI Configuration"])

@router.get("/me", response_model=StandardResponse[OrganizationResponse])
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = OrganizationRepository(db)
    org = await repo.get(current_user.organization_id)
    if not org:
        raise NotFoundError("Organization not found", code="ORG_NOT_FOUND")
    return StandardResponse(data=OrganizationResponse.model_validate(org))

@router.patch("/me", response_model=StandardResponse[OrganizationResponse])
async def update_organization_settings(
    req: OrganizationUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = OrganizationRepository(db)
    org = await repo.get(current_user.organization_id)
    if not org:
        raise NotFoundError("Organization not found", code="ORG_NOT_FOUND")

    if req.name is not None:
        org.name = req.name
    if req.ai_settings is not None:
        current_settings = org.ai_settings or {}
        current_settings.update(req.ai_settings.model_dump(exclude_unset=True))
        org.ai_settings = current_settings

    updated = await repo.update(org)
    return StandardResponse(data=OrganizationResponse.model_validate(updated))
