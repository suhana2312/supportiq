from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.core.security import get_current_user
from backend.app.core.exceptions import NotFoundError, PermissionDeniedError
from backend.app.models.models import User, Order
from backend.app.models.enums import UserRole, OrderStatus
from backend.app.schemas.order import OrderResponse
from backend.app.schemas.common import StandardResponse, PaginatedResponse
from backend.app.repositories.order_repo import OrderRepository

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("", response_model=StandardResponse[PaginatedResponse[OrderResponse]])
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = OrderRepository(db)
    filters = []
    if current_user.role == UserRole.CUSTOMER:
        filters.append(Order.customer_id == current_user.id)
    if status:
        filters.append(Order.status == status)

    items, total = await repo.list_paginated(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        filters=filters,
        order_by=Order.ordered_at.desc()
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return StandardResponse(
        data=PaginatedResponse(
            items=[OrderResponse.model_validate(o) for o in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
    )

@router.get("/number/{order_number}", response_model=StandardResponse[OrderResponse])
async def get_order_by_number(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = OrderRepository(db)
    clean_num = order_number.strip().lstrip("#")
    order = await repo.get_by_number(clean_num, current_user.organization_id)
    if not order:
        raise NotFoundError(f"Order #{order_number} not found", code="ORDER_NOT_FOUND")

    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this order", code="ORDER_ACCESS_DENIED")

    return StandardResponse(data=OrderResponse.model_validate(order))

@router.get("/{order_id}", response_model=StandardResponse[OrderResponse])
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = OrderRepository(db)
    order = await repo.get_by_id_with_items(order_id, current_user.organization_id)
    if not order:
        raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")

    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise PermissionDeniedError("You do not have access to this order", code="ORDER_ACCESS_DENIED")

    return StandardResponse(data=OrderResponse.model_validate(order))
