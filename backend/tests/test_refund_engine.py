import pytest
from datetime import datetime, timedelta, timezone
from backend.app.models.models import Order, Refund
from backend.app.models.enums import OrderStatus, RefundStatus
from backend.app.services.refund_engine import RefundEngine

@pytest.fixture
def engine():
    return RefundEngine(refund_window_days=30, high_value_threshold=500.0)

@pytest.mark.asyncio
async def test_delivered_within_30_days_is_eligible(engine):
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord-1",
        order_number="4521",
        status=OrderStatus.DELIVERED,
        total_amount=120.0,
        currency="USD",
        ordered_at=now - timedelta(days=15),
        delivered_at=now - timedelta(days=10),
        shipping_address="123 Test St"
    )
    result = engine.evaluate_eligibility(order)
    assert result.eligible is True
    assert result.refund_amount == 120.0
    assert result.requires_manual_approval is False
    assert "complies fully with our 30-day" in result.reason

@pytest.mark.asyncio
async def test_delivered_over_30_days_is_ineligible(engine):
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord-2",
        order_number="4524",
        status=OrderStatus.DELIVERED,
        total_amount=80.0,
        currency="USD",
        ordered_at=now - timedelta(days=45),
        delivered_at=now - timedelta(days=40),
        shipping_address="123 Test St"
    )
    result = engine.evaluate_eligibility(order)
    assert result.eligible is False
    assert result.refund_amount == 0.0
    assert "exceeds our standard 30-day" in result.reason

@pytest.mark.asyncio
async def test_cancelled_order_immediate_refund(engine):
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord-3",
        order_number="4522",
        status=OrderStatus.CANCELLED,
        total_amount=95.0,
        currency="USD",
        ordered_at=now - timedelta(days=1),
        shipping_address="123 Test St"
    )
    result = engine.evaluate_eligibility(order)
    assert result.eligible is True
    assert result.refund_amount == 95.0
    assert "cancelled prior to fulfillment" in result.reason

@pytest.mark.asyncio
async def test_duplicate_refund_prevention(engine):
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord-4",
        order_number="4521",
        status=OrderStatus.DELIVERED,
        total_amount=120.0,
        currency="USD",
        ordered_at=now - timedelta(days=10),
        delivered_at=now - timedelta(days=5),
        shipping_address="123 Test St"
    )
    existing_refund = Refund(
        id="ref-active-1",
        organization_id="org-1",
        order_id="ord-4",
        customer_id="cust-1",
        amount=120.0,
        reason="Initial return",
        status=RefundStatus.REQUESTED
    )
    result = engine.evaluate_eligibility(order, existing_refund=existing_refund)
    assert result.eligible is False
    assert "already being processed" in result.reason

@pytest.mark.asyncio
async def test_high_value_refund_requires_manual_approval(engine):
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord-5",
        order_number="4523",
        status=OrderStatus.DELIVERED,
        total_amount=1200.0,
        currency="USD",
        ordered_at=now - timedelta(days=10),
        delivered_at=now - timedelta(days=5),
        shipping_address="123 Test St"
    )
    result = engine.evaluate_eligibility(order)
    assert result.eligible is True
    assert result.requires_manual_approval is True
    assert "manager approval is required" in result.reason

@pytest.mark.asyncio
async def test_damaged_goods_flagged_for_review(engine):
    now = datetime.now(timezone.utc)
    order = Order(
        id="ord-6",
        order_number="4526",
        status=OrderStatus.DELIVERED,
        total_amount=150.0,
        currency="USD",
        ordered_at=now - timedelta(days=10),
        delivered_at=now - timedelta(days=5),
        shipping_address="123 Test St"
    )
    result = engine.evaluate_eligibility(order, customer_reason="Item arrived completely broken and damaged")
    assert result.eligible is True
    assert result.requires_manual_approval is True
    assert "Defective or damaged" in result.reason
