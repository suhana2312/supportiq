from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.models.models import Order, OrderItem, Refund
from backend.app.repositories.base import BaseRepository

class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)

    async def get_by_number(self, order_number: str, organization_id: str) -> Optional[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.refunds))
            .where(
                Order.order_number == order_number,
                Order.organization_id == organization_id
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id_with_items(self, order_id: str, organization_id: str) -> Optional[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.refunds))
            .where(
                Order.id == order_id,
                Order.organization_id == organization_id
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_customer_orders(
        self,
        customer_id: str,
        organization_id: str,
        limit: int = 10
    ) -> List[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.refunds))
            .where(
                Order.customer_id == customer_id,
                Order.organization_id == organization_id
            )
            .order_by(Order.ordered_at.desc())
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # Refund operations
    async def create_refund(self, refund: Refund) -> Refund:
        self.db.add(refund)
        await self.db.commit()
        await self.db.refresh(refund)
        return refund

    async def get_refund_by_order(self, order_id: str) -> Optional[Refund]:
        stmt = select(Refund).where(Refund.order_id == order_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_refunds(self, organization_id: str, limit: int = 50) -> List[Refund]:
        stmt = (
            select(Refund)
            .where(Refund.organization_id == organization_id)
            .order_by(Refund.created_at.desc())
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
