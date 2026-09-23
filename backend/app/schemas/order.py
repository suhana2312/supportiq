from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from backend.app.models.enums import OrderStatus, RefundStatus

class OrderItemResponse(BaseModel):
    id: str
    product_name: str
    quantity: int
    price: float

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    organization_id: str
    customer_id: str
    order_number: str
    status: OrderStatus
    total_amount: float
    currency: str
    ordered_at: datetime
    estimated_delivery: Optional[datetime]
    delivered_at: Optional[datetime]
    shipping_address: str
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

class RefundCheckRequest(BaseModel):
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    reason: Optional[str] = "Customer request"

class RefundCheckResponse(BaseModel):
    eligible: bool
    reason: str
    refund_amount: float
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    requires_manual_approval: bool = False
    policy_citation: Optional[str] = None

class RefundCreateRequest(BaseModel):
    order_id: str
    amount: float
    reason: str

class RefundResponse(BaseModel):
    id: str
    organization_id: str
    order_id: str
    customer_id: str
    amount: float
    reason: str
    status: RefundStatus
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True
