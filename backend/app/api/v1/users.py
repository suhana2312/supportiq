from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.core.security import get_current_user, require_roles, hash_password
from backend.app.core.exceptions import NotFoundError, BusinessRuleViolationError
from backend.app.models.models import User
from backend.app.models.enums import UserRole
from backend.app.schemas.auth import UserResponse, UserCreateAdminRequest, UserUpdateRequest
from backend.app.schemas.common import StandardResponse, PaginatedResponse
from backend.app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=StandardResponse[PaginatedResponse[UserResponse]])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    filters = []
    if role:
        filters.append(User.role == role)

    items, total = await repo.list_paginated(
        organization_id=current_user.organization_id if current_user.role != UserRole.SUPER_ADMIN else None,
        page=page,
        page_size=page_size,
        filters=filters,
        order_by=User.created_at.desc()
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    paginated = PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in items],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )
    return StandardResponse(data=paginated)

@router.post("", response_model=StandardResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreateAdminRequest,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    existing = await repo.get_by_email_any_org(req.email)
    if existing:
        raise BusinessRuleViolationError("Email is already registered", code="EMAIL_EXISTS")

    new_user = User(
        organization_id=current_user.organization_id,
        name=req.name,
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        role=req.role,
        is_active=True
    )
    created = await repo.create(new_user)
    return StandardResponse(data=UserResponse.model_validate(created))

@router.patch("/{user_id}", response_model=StandardResponse[UserResponse])
async def update_user(
    user_id: str,
    req: UserUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    user = await repo.get_by_org(user_id, current_user.organization_id)
    if not user:
        raise NotFoundError("User not found", code="USER_NOT_FOUND")

    if req.name is not None:
        user.name = req.name
    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active

    updated = await repo.update(user)
    return StandardResponse(data=UserResponse.model_validate(updated))
