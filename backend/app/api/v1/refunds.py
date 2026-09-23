from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.core.security import get_current_user, require_roles
from backend.app.core.exceptions import NotFoundError, PermissionDeniedError, BusinessRuleViolationError
from backend.app.models.models import User, Refund, Order
from backend.app.models.enums import UserRole, RefundStatus
from backend.app.schemas.order import (
    RefundCheckRequest, RefundCheckResponse, RefundCreateRequest, RefundResponse
)
from backend.app.schemas.common import StandardResponse, PaginatedResponse
from backend.app.repositories.order_repo import OrderRepository
from backend.app.services.refund_engine import refund_engine

router = APIRouter(prefix="/refunds", tags=["Refunds"])

@router.post("/check-eligibility", response_model=StandardResponse[RefundCheckResponse])
async def check_refund_eligibility(
    req: RefundCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = OrderRepository(db)
    order = None
    if req.order_number:
        clean_num = req.order_number.strip().lstrip("#")
        order = await repo.get_by_number(clean_num, current_user.organization_id)
    elif req.order_id:
        order = await repo.get_by_id_with_items(req.order_id, current_user.organization_id)

    if not order:
        raise NotFoundError("Order could not be found to evaluate refund eligibility", code="ORDER_NOT_FOUND")

    # If customer, enforce ownership
    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise PermissionDeniedError("Cannot check refunds for another customer's order", code="ORDER_FORBIDDEN")

    existing_refund = await repo.get_refund_by_order(order.id)
    result = refund_engine.evaluate_eligibility(
        order=order,
        existing_refund=existing_refund,
        customer_reason=req.reason or ""
    )

    return StandardResponse(
        data=RefundCheckResponse(
            eligible=result.eligible,
            reason=result.reason,
            refund_amount=result.refund_amount,
            order_id=result.order_id,
            order_number=result.order_number,
            requires_manual_approval=result.requires_manual_approval,
            policy_citation=result.policy_citation
        )
    )

@router.post("", response_model=StandardResponse[RefundResponse], status_code=status.HTTP_201_CREATED)
async def request_refund(
    req: RefundCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = OrderRepository(db)
    order = await repo.get_by_id_with_items(req.order_id, current_user.organization_id)
    if not order:
        raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")

    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise PermissionDeniedError("Cannot request refunds for other users", code="ORDER_FORBIDDEN")

    # Check duplicate
    existing = await repo.get_refund_by_order(order.id)
    if existing:
        raise BusinessRuleViolationError("A refund request has already been filed for this order", code="DUPLICATE_REFUND")

    # Evaluate eligibility
    eligibility = refund_engine.evaluate_eligibility(order, existing, req.reason)
    if not eligibility.eligible and not eligibility.requires_manual_approval:
        raise BusinessRuleViolationError(f"Refund ineligible: {eligibility.reason}", code="REFUND_INELIGIBLE")

    initial_status = RefundStatus.PROCESSING if eligibility.eligible and not eligibility.requires_manual_approval else RefundStatus.REQUESTED
    refund = Refund(
        organization_id=current_user.organization_id,
        order_id=order.id,
        customer_id=order.customer_id,
        amount=req.amount or order.total_amount,
        reason=req.reason,
        status=initial_status
    )
    created = await repo.create_refund(refund)
    return StandardResponse(data=RefundResponse.model_validate(created))

@router.get("", response_model=StandardResponse[List[RefundResponse]])
async def list_refunds(
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = OrderRepository(db)
    refunds = await repo.list_refunds(current_user.organization_id)
    return StandardResponse(data=[RefundResponse.model_validate(r) for r in refunds])

@router.patch("/{refund_id}/status", response_model=StandardResponse[RefundResponse])
async def update_refund_status(
    refund_id: str,
    status_update: RefundStatus,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.future import select
    res = await db.execute(select(Refund).where(Refund.id == refund_id, Refund.organization_id == current_user.organization_id))
    refund = res.scalar_one_or_none()
    if not refund:
        raise NotFoundError("Refund not found", code="REFUND_NOT_FOUND")

    refund.status = status_update
    if status_update in [RefundStatus.APPROVED, RefundStatus.COMPLETED]:
        refund.processed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(refund)
    return StandardResponse(data=RefundResponse.model_validate(refund))
