from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.models import SupportTicket
from backend.app.models.enums import TicketPriority, TicketStatus
from backend.app.repositories.ticket_repo import TicketRepository

async def escalate_to_human(
    customer_id: str,
    organization_id: str,
    conversation_id: Optional[str],
    reason: str,
    ai_summary: str,
    db: AsyncSession,
    priority: TicketPriority = TicketPriority.HIGH
) -> Dict[str, Any]:
    """
    Tool 6: Automatically escalates an issue to human agents with status ESCALATED.
    """
    repo = TicketRepository(db)
    ticket = SupportTicket(
        organization_id=organization_id,
        customer_id=customer_id,
        conversation_id=conversation_id,
        subject=f"Human Escalation: {reason[:80]}",
        description=f"Escalation Request.\nReason: {reason}\nAI Context Summary: {ai_summary}",
        priority=priority,
        status=TicketStatus.ESCALATED,
        ai_summary=ai_summary
    )
    created = await repo.create(ticket)
    return {
        "ticket_id": created.id,
        "status": created.status.value,
        "priority": created.priority.value,
        "message": "A priority support ticket has been created and transferred to our human support team."
    }
