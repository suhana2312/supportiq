from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.models.enums import MessageSender

class CitationResponse(BaseModel):
    id: Optional[str] = None
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    document_name: str
    relevance_score: float
    page_number: int

    class Config:
        from_attributes = True

class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_type: MessageSender
    content: str
    metadata_json: Dict[str, Any] = {}
    created_at: datetime
    citations: List[CitationResponse] = []

    class Config:
        from_attributes = True

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = "Support Conversation"

class ConversationResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class FeedbackCreateRequest(BaseModel):
    conversation_id: str
    message_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: str
    conversation_id: str
    message_id: Optional[str]
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class StreamEvent(BaseModel):
    event: str  # "token", "tool_call", "citation", "done", "error"
    data: Dict[str, Any]
