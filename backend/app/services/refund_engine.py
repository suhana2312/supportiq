from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass
from backend.app.core.config import settings
from backend.app.models.models import Order, Refund
from backend.app.models.enums import OrderStatus, RefundStatus

@dataclass
class RefundEligibilityResult:
    eligible: bool
    reason: str
    refund_amount: float
    order_id: str
    order_number: str
    requires_manual_approval: bool = False
    policy_citation: str = "Refund Policy — Section 3: Standard Return Window"

class RefundEngine:
    def __init__(
        self,
        refund_window_days: int = settings.REFUND_WINDOW_DAYS,
        high_value_threshold: float = settings.HIGH_VALUE_REFUND_THRESHOLD
    ):
        self.refund_window_days = refund_window_days
        self.high_value_threshold = high_value_threshold

    def evaluate_eligibility(
        self,
        order: Order,
        existing_refund: Optional[Refund] = None,
        customer_reason: str = ""
    ) -> RefundEligibilityResult:
        """
        Deterministic Python business logic for refund checks.
        NEVER leaves financial authorization decisions to an LLM.
        """
        # Rule 1: Check existing refund requests to prevent duplicates
        if existing_refund:
            if existing_refund.status in [RefundStatus.REQUESTED, RefundStatus.PROCESSING]:
                return RefundEligibilityResult(
                    eligible=False,
                    reason=f"An active refund request ({existing_refund.id[:8]}) is already being processed for this order.",
                    refund_amount=0.0,
                    order_id=order.id,
                    order_number=order.order_number,
                    requires_manual_approval=False,
                    policy_citation="Refund Policy — Section 1.4: Duplicate Refund Prevention"
                )
            if existing_refund.status in [RefundStatus.APPROVED, RefundStatus.COMPLETED]:
                return RefundEligibilityResult(
                    eligible=False,
                    reason="This order has already been fully refunded.",
                    refund_amount=0.0,
                    order_id=order.id,
                    order_number=order.order_number,
                    requires_manual_approval=False,
                    policy_citation="Refund Policy — Section 1.4: Settlement Completion"
                )

        # Rule 2: Order was cancelled before shipment -> 100% eligible
        if order.status == OrderStatus.CANCELLED:
            return RefundEligibilityResult(
                eligible=True,
                reason="Order was cancelled prior to fulfillment and is eligible for immediate 100% refund.",
                refund_amount=order.total_amount,
                order_id=order.id,
                order_number=order.order_number,
                requires_manual_approval=False,
                policy_citation="Refund Policy — Section 2: Order Cancellation & Pre-Shipment Reversals"
            )

        # Rule 3: Order is currently in transit or processing
        if order.status in [OrderStatus.PENDING, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY]:
            # If customer claims not received or damaged
            lower_reason = customer_reason.lower()
            if any(term in lower_reason for term in ["lost", "not arrived", "never arrived", "missing", "delayed"]):
                return RefundEligibilityResult(
                    eligible=False,
                    reason=f"Order is currently in {order.status.value} status. A delivery delay inquiry has been flagged for support agent verification.",
                    refund_amount=order.total_amount,
                    order_id=order.id,
                    order_number=order.order_number,
                    requires_manual_approval=True,
                    policy_citation="Shipping Policy — Section 4: In-Transit Loss & Delivery Discrepancies"
                )
            else:
                return RefundEligibilityResult(
                    eligible=False,
                    reason=f"Order is currently '{order.status.value}'. Items must be delivered and returned before a standard refund can be issued.",
                    refund_amount=0.0,
                    order_id=order.id,
                    order_number=order.order_number,
                    requires_manual_approval=False,
                    policy_citation="Refund Policy — Section 3.1: Pre-Delivery Refund Restrictions"
                )

        # Rule 4: Order is DELIVERED -> verify 30-day window
        if order.status == OrderStatus.DELIVERED:
            if not order.delivered_at:
                # If delivered_at not explicitly stamped, fallback to ordered_at
                delivery_time = order.ordered_at
            else:
                delivery_time = order.delivered_at

            now = datetime.now(timezone.utc)
            # Ensure timezone-aware difference
            if delivery_time.tzinfo is None:
                delivery_time = delivery_time.replace(tzinfo=timezone.utc)

            days_since_delivery = (now - delivery_time).days

            if days_since_delivery > self.refund_window_days:
                return RefundEligibilityResult(
                    eligible=False,
                    reason=f"Delivery occurred {days_since_delivery} days ago, which exceeds our standard {self.refund_window_days}-day return and refund policy window.",
                    refund_amount=0.0,
                    order_id=order.id,
                    order_number=order.order_number,
                    requires_manual_approval=False,
                    policy_citation=f"Refund Policy — Section 3: Standard {self.refund_window_days}-Day Return Window"
                )

            # Check if high value requires manual approval
            if order.total_amount >= self.high_value_threshold:
                return RefundEligibilityResult(
                    eligible=True,
                    reason=f"Order was delivered {days_since_delivery} days ago (within the {self.refund_window_days}-day window). Because the amount (${order.total_amount:.2f}) exceeds the ${self.high_value_threshold:.2f} threshold, manager approval is required.",
                    refund_amount=order.total_amount,
                    order_id=order.id,
                    order_number=order.order_number,
                    requires_manual_approval=True,
                    policy_citation="Refund Policy — Section 5: High-Value Transaction Approvals"
                )

            # Check if reason mentions damage/defect
            lower_reason = customer_reason.lower()
            if any(term in lower_reason for term in ["damaged", "broken", "defective", "wrong item"]):
                return RefundEligibilityResult(
                    eligible=True,
                    reason=f"Order is within the return window. Defective or damaged merchandise claims qualify for full reimbursement upon photo review.",
                    refund_amount=order.total_amount,
                    order_id=order.id,
                    order_number=order.order_number,
                    requires_manual_approval=True,
                    policy_citation="Refund Policy — Section 4: Defective and Damaged Goods"
                )

            # Standard approved refund
            return RefundEligibilityResult(
                eligible=True,
                reason=f"Order was delivered {days_since_delivery} days ago and complies fully with our {self.refund_window_days}-day return guidelines.",
                refund_amount=order.total_amount,
                order_id=order.id,
                order_number=order.order_number,
                requires_manual_approval=False,
                policy_citation="Refund Policy — Section 3: Standard Return Window"
            )

        # Fallback
        return RefundEligibilityResult(
            eligible=False,
            reason=f"Order status '{order.status.value}' cannot be automatically processed for refund. Requires support staff evaluation.",
            refund_amount=0.0,
            order_id=order.id,
            order_number=order.order_number,
            requires_manual_approval=True,
            policy_citation="Refund Policy — Section 7: Exceptional Inquiries"
        )

refund_engine = RefundEngine()
