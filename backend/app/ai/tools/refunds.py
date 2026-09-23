from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.order_repo import OrderRepository
from backend.app.services.refund_engine import refund_engine

async def check_refund_eligibility(
    order_number_or_id: str,
    organization_id: str,
    db: AsyncSession,
    reason: str = "Customer requested refund"
) -> Dict[str, Any]:
    """
    Tool 4: Evaluates refund eligibility strictly via the deterministic Refund Engine.
    Does NOT hallucinate policies.
    """
    repo = OrderRepository(db)
    clean_id = order_number_or_id.strip().lstrip("#")
    
    # Try finding by number first, then by id
    order = await repo.get_by_number(clean_id, organization_id)
    if not order:
        order = await repo.get_by_id_with_items(clean_id, organization_id)
        
    if not order:
        return {
            "eligible": False,
            "reason": f"Order '{order_number_or_id}' was not found in our records.",
            "refund_amount": 0.0,
            "order_number": order_number_or_id,
            "requires_manual_approval": False,
            "policy_citation": "Refund Policy — Section 1: Record Verification"
        }

    existing_refund = await repo.get_refund_by_order(order.id)
    result = refund_engine.evaluate_eligibility(
        order=order,
        existing_refund=existing_refund,
        customer_reason=reason
    )

    return {
        "eligible": result.eligible,
        "reason": result.reason,
        "refund_amount": result.refund_amount,
        "order_id": result.order_id,
        "order_number": result.order_number,
        "requires_manual_approval": result.requires_manual_approval,
        "policy_citation": result.policy_citation
    }
