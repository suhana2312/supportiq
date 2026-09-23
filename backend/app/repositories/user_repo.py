from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.models import User, RefreshToken
from backend.app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email_and_org(self, email: str, organization_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(
                User.email == email.lower(),
                User.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email_any_org(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalars().first()

    async def save_refresh_token(self, token_obj: RefreshToken) -> RefreshToken:
        self.db.add(token_obj)
        await self.db.commit()
        await self.db.refresh(token_obj)
        return token_obj

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_obj: RefreshToken, revoked_at) -> None:
        token_obj.revoked_at = revoked_at
        await self.db.commit()
