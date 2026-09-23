from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AISettingsSchema(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    chunk_size: int = Field(default=1000, ge=100, le=3000)
    chunk_overlap: int = Field(default=150, ge=0, le=500)
    similarity_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    max_response_tokens: int = Field(default=1000, ge=100, le=4000)
    auto_escalation_threshold: float = Field(default=0.60, ge=0.0, le=1.0)

class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    ai_settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = None
    ai_settings: Optional[AISettingsSchema] = None
