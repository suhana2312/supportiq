from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.core.security import get_current_user, require_roles
from backend.app.core.exceptions import NotFoundError, PermissionDeniedError
from backend.app.models.models import User, SupportTicket, TicketMessage
from backend.app.models.enums import UserRole, TicketStatus, TicketPriority
from backend.app.schemas.ticket import (
    TicketCreateRequest, TicketUpdateRequest, TicketResponse, TicketMessageCreateRequest,
    TicketMessageResponse, TicketEscalateRequest
)
from backend.app.schemas.common import StandardResponse, PaginatedResponse
from backend.app.repositories.ticket_repo import TicketRepository

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])

@router.post("", response_model=StandardResponse[TicketResponse], status_code=status.HTTP_201_CREATED)
async def create_ticket(
    req: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = TicketRepository(db)
    ticket = SupportTicket(
        organization_id=current_user.organization_id,
        customer_id=current_user.id,
        conversation_id=req.conversation_id,
        subject=req.subject,
        description=req.description,
        priority=req.priority,
        status=TicketStatus.OPEN
    )
    created = await repo.create(ticket)
    # Add initial message
    msg = TicketMessage(
        ticket_id=created.id,
        sender_id=current_user.id,
        sender_type="CUSTOMER" if current_user.role == UserRole.CUSTOMER else "SUPPORT_AGENT",
        message=req.description,
        is_internal_note=False
    )
    await repo.add_message(msg)

    detailed = await repo.get_with_details(created.id, current_user.organization_id)
    return StandardResponse(data=TicketResponse.model_validate(detailed))

@router.get("", response_model=StandardResponse[PaginatedResponse[TicketResponse]])
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = TicketRepository(db)
    customer_filter = current_user.id if current_user.role == UserRole.CUSTOMER else None

    items, total = await repo.list_tickets(
        organization_id=current_user.organization_id,
        customer_id=customer_filter,
        status=status,
        priority=priority,
        page=page,
        page_size=page_size
    )

    ticket_responses = []
    for t in items:
        resp = TicketResponse.model_validate(t)
        resp.customer_name = t.customer.name if t.customer else "Unknown"
        resp.assigned_agent_name = t.assigned_agent.name if t.assigned_agent else "Unassigned"
        ticket_responses.append(resp)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return StandardResponse(
        data=PaginatedResponse(
            items=ticket_responses,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
    )

@router.get("/{ticket_id}", response_model=StandardResponse[TicketResponse])
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = TicketRepository(db)
    ticket = await repo.get_with_details(ticket_id, current_user.organization_id)
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")

    if current_user.role == UserRole.CUSTOMER and ticket.customer_id != current_user.id:
        raise PermissionDeniedError("Access to other users' tickets is forbidden", code="TICKET_FORBIDDEN")

    resp = TicketResponse.model_validate(ticket)
    resp.customer_name = ticket.customer.name if ticket.customer else "Unknown"
    resp.assigned_agent_name = ticket.assigned_agent.name if ticket.assigned_agent else "Unassigned"
    
    # Hide internal notes from customer
    if current_user.role == UserRole.CUSTOMER:
        resp.messages = [m for m in resp.messages if not m.is_internal_note]

    return StandardResponse(data=resp)

@router.patch("/{ticket_id}", response_model=StandardResponse[TicketResponse])
async def update_ticket(
    ticket_id: str,
    req: TicketUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = TicketRepository(db)
    ticket = await repo.get_with_details(ticket_id, current_user.organization_id)
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")

    if req.status is not None:
        ticket.status = req.status
        if req.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            ticket.resolved_at = datetime.now(timezone.utc)
    if req.priority is not None:
        ticket.priority = req.priority
    if req.assigned_agent_id is not None:
        ticket.assigned_agent_id = req.assigned_agent_id

    updated = await repo.update(ticket)
    refreshed = await repo.get_with_details(ticket.id, current_user.organization_id)
    return StandardResponse(data=TicketResponse.model_validate(refreshed))

@router.post("/{ticket_id}/messages", response_model=StandardResponse[TicketMessageResponse])
async def add_ticket_message(
    ticket_id: str,
    req: TicketMessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = TicketRepository(db)
    ticket = await repo.get_by_org(ticket_id, current_user.organization_id)
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")

    if current_user.role == UserRole.CUSTOMER:
        if ticket.customer_id != current_user.id:
            raise PermissionDeniedError("Cannot post to other customers' tickets", code="TICKET_FORBIDDEN")
        # Customers cannot post internal notes
        req.is_internal_note = False
        sender_type = "CUSTOMER"
        # Update ticket status if customer replies
        if ticket.status == TicketStatus.WAITING_FOR_CUSTOMER:
            ticket.status = TicketStatus.IN_PROGRESS
            await repo.update(ticket)
    else:
        sender_type = "SUPPORT_AGENT"

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_type=sender_type,
        message=req.message,
        is_internal_note=req.is_internal_note
    )
    created = await repo.add_message(msg)
    
    resp = TicketMessageResponse.model_validate(created)
    resp.sender_name = current_user.name
    return StandardResponse(data=resp)

@router.post("/{ticket_id}/escalate", response_model=StandardResponse[TicketResponse])
async def escalate_ticket(
    ticket_id: str,
    req: TicketEscalateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = TicketRepository(db)
    ticket = await repo.get_with_details(ticket_id, current_user.organization_id)
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")

    ticket.status = TicketStatus.ESCALATED
    ticket.priority = TicketPriority.URGENT
    await repo.update(ticket)

    # Add system audit message
    audit_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_type="SYSTEM",
        message=f"Ticket escalated to high-priority queue. Reason: {req.reason}",
        is_internal_note=True
    )
    await repo.add_message(audit_msg)

    refreshed = await repo.get_with_details(ticket.id, current_user.organization_id)
    return StandardResponse(data=TicketResponse.model_validate(refreshed))

@router.post("/{ticket_id}/resolve", response_model=StandardResponse[TicketResponse])
async def resolve_ticket(
    ticket_id: str,
    current_user: User = Depends(require_roles([UserRole.ORGANIZATION_ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = TicketRepository(db)
    ticket = await repo.get_with_details(ticket_id, current_user.organization_id)
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")

    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.now(timezone.utc)
    await repo.update(ticket)

    return StandardResponse(data=TicketResponse.model_validate(ticket))
