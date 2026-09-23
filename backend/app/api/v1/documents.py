import os
import shutil
import uuid
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db, AsyncSessionLocal
from backend.app.core.config import settings
from backend.app.core.security import get_current_user, require_roles
from backend.app.core.exceptions import NotFoundError, BusinessRuleViolationError, DocumentProcessingError
from backend.app.models.models import User, Document, DocumentChunk, FAQ
from backend.app.models.enums import UserRole, DocumentStatus
from backend.app.schemas.document import (
    DocumentResponse, DocumentChunkResponse, FAQCreateRequest, FAQUpdateRequest, FAQResponse
)
from backend.app.schemas.common import StandardResponse, PaginatedResponse
from backend.app.repositories.document_repo import DocumentRepository
from backend.app.services.document_service import DocumentProcessor

router = APIRouter(prefix="/documents", tags=["Knowledge Base & Documents"])

async def background_process_doc(document_id: str):
    async with AsyncSessionLocal() as session:
        processor = DocumentProcessor(session)
        try:
            await processor.process_document(document_id)
        except Exception:
            pass

@router.post("", response_model=StandardResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    # 1. Validate file extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise BusinessRuleViolationError(
            f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            code="INVALID_FILE_TYPE"
        )

    # 2. Generate safe storage filename
    safe_filename = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    storage_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # 3. Read and validate size
    contents = await file.read()
    file_size = len(contents)
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise BusinessRuleViolationError(
            f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed limit of 15MB",
            code="FILE_TOO_LARGE"
        )

    # Write file to disk
    with open(storage_path, "wb") as f:
        f.write(contents)

    repo = DocumentRepository(db)
    doc = Document(
        organization_id=current_user.organization_id,
        filename=file.filename or "uploaded_file",
        file_type=ext,
        file_size=file_size,
        storage_path=storage_path,
        status=DocumentStatus.UPLOADED,
        uploaded_by=current_user.id
    )
    created_doc = await repo.create(doc)

    # Schedule background document extraction & chunking
    background_tasks.add_task(background_process_doc, created_doc.id)

    return StandardResponse(data=DocumentResponse.model_validate(created_doc))

@router.get("", response_model=StandardResponse[PaginatedResponse[DocumentResponse]])
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN, UserRole.SUPPORT_AGENT])),
    db: AsyncSession = Depends(get_db)
):
    repo = DocumentRepository(db)
    filters = []
    if status:
        filters.append(Document.status == status)

    items, total = await repo.list_paginated(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        filters=filters,
        order_by=Document.created_at.desc()
    )

    doc_responses = []
    for d in items:
        resp = DocumentResponse.model_validate(d)
        resp.chunk_count = len(d.chunks) if d.chunks else 0
        doc_responses.append(resp)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return StandardResponse(
        data=PaginatedResponse(
            items=doc_responses,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
    )

@router.get("/{document_id}", response_model=StandardResponse[DocumentResponse])
async def get_document(
    document_id: str,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN, UserRole.SUPPORT_AGENT])),
    db: AsyncSession = Depends(get_db)
):
    repo = DocumentRepository(db)
    doc = await repo.get_by_org(document_id, current_user.organization_id)
    if not doc:
        raise NotFoundError("Document not found or does not belong to your organization", code="DOCUMENT_NOT_FOUND")
    return StandardResponse(data=DocumentResponse.model_validate(doc))

@router.delete("/{document_id}", response_model=StandardResponse[dict])
async def delete_document(
    document_id: str,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = DocumentRepository(db)
    doc = await repo.get_by_org(document_id, current_user.organization_id)
    if not doc:
        raise NotFoundError("Document not found", code="DOCUMENT_NOT_FOUND")

    # Remove storage file if exists
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    await repo.delete(doc)
    return StandardResponse(data={"message": "Document and all its vector chunks deleted successfully"})

@router.post("/{document_id}/reprocess", response_model=StandardResponse[dict])
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = DocumentRepository(db)
    doc = await repo.get_by_org(document_id, current_user.organization_id)
    if not doc:
        raise NotFoundError("Document not found", code="DOCUMENT_NOT_FOUND")

    doc.status = DocumentStatus.PROCESSING
    doc.error_message = None
    await repo.update(doc)

    background_tasks.add_task(background_process_doc, doc.id)
    return StandardResponse(data={"message": "Document reprocessing started in background"})

# FAQs Endpoints
@router.get("/faqs/list", response_model=StandardResponse[List[FAQResponse]])
async def list_faqs(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = DocumentRepository(db)
    faqs = await repo.get_faqs(current_user.organization_id, category=category)
    return StandardResponse(data=[FAQResponse.model_validate(f) for f in faqs])

@router.post("/faqs", response_model=StandardResponse[FAQResponse], status_code=status.HTTP_201_CREATED)
async def create_faq(
    req: FAQCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    faq = FAQ(
        organization_id=current_user.organization_id,
        question=req.question,
        answer=req.answer,
        category=req.category
    )
    db.add(faq)
    await db.commit()
    await db.refresh(faq)
    return StandardResponse(data=FAQResponse.model_validate(faq))

@router.delete("/faqs/{faq_id}", response_model=StandardResponse[dict])
async def delete_faq(
    faq_id: str,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = DocumentRepository(db)
    from sqlalchemy.future import select
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id, FAQ.organization_id == current_user.organization_id))
    faq = result.scalar_one_or_none()
    if not faq:
        raise NotFoundError("FAQ not found", code="FAQ_NOT_FOUND")

    await db.delete(faq)
    await db.commit()
    return StandardResponse(data={"message": "FAQ deleted successfully"})
