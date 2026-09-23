from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.models import SupportTicket
from backend.app.models.enums import TicketPriority, TicketStatus
from backend.app.repositories.ticket_repo import TicketRepository

async def create_support_ticket(
    customer_id: str,
    organization_id: str,
    subject: str,
    description: str,
    priority: TicketPriority,
    db: AsyncSession,
    conversation_id: Optional[str] = None,
    ai_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tool 5: Creates an official support ticket and records the AI context.
    """
    repo = TicketRepository(db)
    ticket = SupportTicket(
        organization_id=organization_id,
        customer_id=customer_id,
        conversation_id=conversation_id,
        subject=subject,
        description=description,
        priority=priority,
        status=TicketStatus.OPEN,
        ai_summary=ai_summary
    )
    created = await repo.create(ticket)
    return {
        "ticket_id": created.id,
        "subject": created.subject,
        "priority": created.priority.value,
        "status": created.status.value,
        "created_at": created.created_at.isoformat()
    }

async def get_ticket_status(
    ticket_id: str,
    organization_id: str,
    db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    Tool 7: Retrieves the status and agent assignment for a support ticket.
    """
    repo = TicketRepository(db)
    ticket = await repo.get_with_details(ticket_id, organization_id)
    if not ticket:
        return None
    return {
        "ticket_id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status.value,
        "priority": ticket.priority.value,
        "assigned_agent": ticket.assigned_agent.name if ticket.assigned_agent else "Unassigned",
        "created_at": ticket.created_at.isoformat(),
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
    }
