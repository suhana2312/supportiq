from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.app.models.enums import TicketPriority, TicketStatus

class TicketMessageCreateRequest(BaseModel):
    message: str = Field(min_length=1)
    is_internal_note: bool = False

class TicketMessageResponse(BaseModel):
    id: str
    ticket_id: str
    sender_id: str
    sender_type: str
    message: str
    is_internal_note: bool
    created_at: datetime
    sender_name: Optional[str] = None

    class Config:
        from_attributes = True

class TicketCreateRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    priority: TicketPriority = TicketPriority.MEDIUM
    conversation_id: Optional[str] = None

class TicketUpdateRequest(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[str] = None

class TicketEscalateRequest(BaseModel):
    reason: str = Field(default="Customer requested human agent escalation")
    conversation_id: Optional[str] = None

class TicketResponse(BaseModel):
    id: str
    organization_id: str
    customer_id: str
    conversation_id: Optional[str]
    assigned_agent_id: Optional[str]
    subject: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    ai_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    customer_name: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    messages: List[TicketMessageResponse] = []

    class Config:
        from_attributes = True
