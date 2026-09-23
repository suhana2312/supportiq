from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.app.models.enums import DocumentStatus

class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    content: str
    page_number: int
    chunk_index: int
    metadata_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    organization_id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    uploaded_by: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    chunk_count: Optional[int] = 0

    class Config:
        from_attributes = True

class FAQCreateRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    answer: str = Field(min_length=5)
    category: str = Field(default="General", max_length=100)

class FAQUpdateRequest(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None

class FAQResponse(BaseModel):
    id: str
    organization_id: str
    question: str
    answer: str
    category: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
