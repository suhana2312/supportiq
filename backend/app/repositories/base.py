from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update, delete
from backend.app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: str) -> Optional[ModelType]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_by_org(self, id: str, organization_id: str) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.db.delete(obj)
        await self.db.commit()

    async def list_paginated(
        self,
        organization_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List[Any]] = None,
        order_by: Optional[Any] = None
    ) -> tuple[List[ModelType], int]:
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        all_filters = []
        if organization_id and hasattr(self.model, "organization_id"):
            all_filters.append(self.model.organization_id == organization_id)
        if filters:
            all_filters.extend(filters)

        if all_filters:
            query = query.where(*all_filters)
            count_query = count_query.where(*all_filters)

        if order_by is not None:
            query = query.order_by(order_by)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        items_res = await self.db.execute(query)
        items = list(items_res.scalars().all())

        return items, total
