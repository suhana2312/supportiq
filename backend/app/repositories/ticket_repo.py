from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from backend.app.models.models import SupportTicket, TicketMessage, User
from backend.app.models.enums import TicketStatus, TicketPriority
from backend.app.repositories.base import BaseRepository

class TicketRepository(BaseRepository[SupportTicket]):
    def __init__(self, db: AsyncSession):
        super().__init__(SupportTicket, db)

    async def get_with_details(self, ticket_id: str, organization_id: str) -> Optional[SupportTicket]:
        stmt = (
            select(SupportTicket)
            .options(
                selectinload(SupportTicket.customer),
                selectinload(SupportTicket.assigned_agent),
                selectinload(SupportTicket.messages).selectinload(TicketMessage.sender)
            )
            .where(
                SupportTicket.id == ticket_id,
                SupportTicket.organization_id == organization_id
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_tickets(
        self,
        organization_id: str,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SupportTicket], int]:
        filters = [SupportTicket.organization_id == organization_id]
        if customer_id:
            filters.append(SupportTicket.customer_id == customer_id)
        if agent_id:
            filters.append(SupportTicket.assigned_agent_id == agent_id)
        if status:
            filters.append(SupportTicket.status == status)
        if priority:
            filters.append(SupportTicket.priority == priority)

        count_stmt = select(func.count()).select_from(SupportTicket).where(*filters)
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            select(SupportTicket)
            .options(
                selectinload(SupportTicket.customer),
                selectinload(SupportTicket.assigned_agent)
            )
            .where(*filters)
            .order_by(SupportTicket.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items_res = await self.db.execute(stmt)
        items = list(items_res.scalars().all())

        return items, total

    async def add_message(self, message: TicketMessage) -> TicketMessage:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
