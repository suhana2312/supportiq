import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.core.security import get_current_user
from backend.app.core.exceptions import NotFoundError, PermissionDeniedError
from backend.app.models.models import User, Conversation, Feedback
from backend.app.models.enums import UserRole
from backend.app.schemas.chat import (
    ConversationCreateRequest, ConversationResponse, MessageCreateRequest, MessageResponse,
    CitationResponse, FeedbackCreateRequest, FeedbackResponse
)
from backend.app.schemas.common import StandardResponse, PaginatedResponse
from backend.app.repositories.conversation_repo import ConversationRepository
from backend.app.ai.agent import SupportAgentService

router = APIRouter(prefix="/conversations", tags=["Chat & Conversations"])

@router.post("", response_model=StandardResponse[ConversationResponse], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ConversationRepository(db)
    conv = Conversation(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=req.title or "Support Conversation",
        status="ACTIVE"
    )
    created = await repo.create(conv)
    return StandardResponse(data=ConversationResponse.model_validate(created))

@router.get("", response_model=StandardResponse[PaginatedResponse[ConversationResponse]])
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ConversationRepository(db)
    # If customer, only show their own conversations. Admins/Agents can see all org conversations.
    user_id_filter = current_user.id if current_user.role == UserRole.CUSTOMER else None

    items, total = await repo.list_conversations(
        organization_id=current_user.organization_id,
        user_id=user_id_filter,
        page=page,
        page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return StandardResponse(
        data=PaginatedResponse(
            items=[ConversationResponse.model_validate(c) for c in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
    )

@router.get("/{conversation_id}", response_model=StandardResponse[ConversationResponse])
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ConversationRepository(db)
    conv = await repo.get_with_messages(conversation_id, current_user.organization_id)
    if not conv:
        raise NotFoundError("Conversation not found", code="CONVERSATION_NOT_FOUND")

    # If customer, prevent accessing another customer's conversation in the same org
    if current_user.role == UserRole.CUSTOMER and conv.user_id != current_user.id:
        raise PermissionDeniedError("Cannot access conversations of other users", code="CONVERSATION_FORBIDDEN")

    return StandardResponse(data=ConversationResponse.model_validate(conv))

@router.post("/{conversation_id}/messages", response_model=StandardResponse[MessageResponse])
async def send_message(
    conversation_id: str,
    req: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_org(conversation_id, current_user.organization_id)
    if not conv:
        raise NotFoundError("Conversation not found", code="CONVERSATION_NOT_FOUND")

    if current_user.role == UserRole.CUSTOMER and conv.user_id != current_user.id:
        raise PermissionDeniedError("Cannot post to other users' conversations", code="CONVERSATION_FORBIDDEN")

    agent_service = SupportAgentService(db)
    result = await agent_service.get_response_sync(
        conversation_id=conversation_id,
        user_message=req.content,
        user=current_user
    )

    from backend.app.models.models import Message
    from sqlalchemy.future import select
    msg_res = await db.execute(select(Message).where(Message.id == result["message_id"]))
    saved_msg = msg_res.scalar_one()

    return StandardResponse(data=MessageResponse.model_validate(saved_msg))

@router.get("/{conversation_id}/stream")
async def stream_conversation_response(
    conversation_id: str,
    message: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_org(conversation_id, current_user.organization_id)
    if not conv:
        raise NotFoundError("Conversation not found", code="CONVERSATION_NOT_FOUND")

    if current_user.role == UserRole.CUSTOMER and conv.user_id != current_user.id:
        raise PermissionDeniedError("Cannot stream to other users' conversations", code="CONVERSATION_FORBIDDEN")

    agent_service = SupportAgentService(db)
    return StreamingResponse(
        agent_service.stream_chat_response(conversation_id, message, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/feedback", response_model=StandardResponse[FeedbackResponse])
async def submit_feedback(
    req: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_org(req.conversation_id, current_user.organization_id)
    if not conv:
        raise NotFoundError("Conversation not found", code="CONVERSATION_NOT_FOUND")

    feedback = Feedback(
        conversation_id=req.conversation_id,
        message_id=req.message_id,
        rating=req.rating,
        comment=req.comment
    )
    created = await repo.add_feedback(feedback)
    return StandardResponse(data=FeedbackResponse.model_validate(created))
