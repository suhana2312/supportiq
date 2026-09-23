from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from backend.app.models.models import Conversation, Message, Citation, Feedback
from backend.app.repositories.base import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Conversation, db)

    async def get_with_messages(self, conversation_id: str, organization_id: str) -> Optional[Conversation]:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.messages).selectinload(Message.citations),
                selectinload(Conversation.feedback)
            )
            .where(
                Conversation.id == conversation_id,
                Conversation.organization_id == organization_id
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_conversations(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Conversation], int]:
        filters = [Conversation.organization_id == organization_id]
        if user_id:
            filters.append(Conversation.user_id == user_id)

        count_stmt = select(func.count()).select_from(Conversation).where(*filters)
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            select(Conversation)
            .where(*filters)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items_res = await self.db.execute(stmt)
        items = list(items_res.scalars().all())

        return items, total

    async def add_message(self, message: Message) -> Message:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def add_citations(self, citations: List[Citation]) -> None:
        self.db.add_all(citations)
        await self.db.commit()

    async def add_feedback(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback
