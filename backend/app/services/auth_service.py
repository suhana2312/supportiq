from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, hash_token
)
from backend.app.core.exceptions import AuthenticationError, BusinessRuleViolationError, NotFoundError
from backend.app.models.models import User, Organization, RefreshToken
from backend.app.models.enums import UserRole
from backend.app.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, RefreshTokenRequest, TokenResponse, UserResponse
)
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.organization_repo import OrganizationRepository
import re

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "org"

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def register(self, req: UserRegisterRequest) -> TokenResponse:
        # Check if email is already taken
        existing_user = await self.user_repo.get_by_email_any_org(req.email)
        if existing_user:
            raise BusinessRuleViolationError("An account with this email address already exists", code="EMAIL_EXISTS")

        # Create Organization
        base_slug = slugify(req.organization_name)
        slug = base_slug
        counter = 1
        while await self.org_repo.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(
            name=req.organization_name,
            slug=slug,
            ai_settings={
                "model": settings.DEFAULT_LLM_MODEL,
                "temperature": 0.2,
                "retrieval_top_k": settings.RETRIEVAL_TOP_K,
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
                "auto_escalation_threshold": settings.AUTO_ESCALATION_THRESHOLD
            }
        )
        created_org = await self.org_repo.create(org)

        # Create User as ORGANIZATION_ADMIN
        pwd_hash = hash_password(req.password)
        user = User(
            organization_id=created_org.id,
            name=req.name,
            email=req.email.lower(),
            password_hash=pwd_hash,
            role=UserRole.ORGANIZATION_ADMIN,
            is_active=True
        )
        created_user = await self.user_repo.create(user)

        # Generate tokens
        token_data = {"sub": created_user.id, "org_id": created_org.id, "role": created_user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Save refresh token in DB
        refresh_exp = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        token_record = RefreshToken(
            user_id=created_user.id,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_exp
        )
        await self.user_repo.save_refresh_token(token_record)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(created_user)
        )

    async def login(self, req: UserLoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email_any_org(req.email)
        if not user or not verify_password(req.password, user.password_hash):
            raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")
        if not user.is_active:
            raise AuthenticationError("Account has been deactivated", code="ACCOUNT_DEACTIVATED")

        token_data = {"sub": user.id, "org_id": user.organization_id, "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        refresh_exp = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_exp
        )
        await self.user_repo.save_refresh_token(token_record)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    async def refresh_token(self, req: RefreshTokenRequest) -> TokenResponse:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type for refresh", code="INVALID_REFRESH_TOKEN")

        user_id = payload.get("sub")
        tok_hash = hash_token(req.refresh_token)
        saved_token = await self.user_repo.get_refresh_token(tok_hash)
        if not saved_token:
            raise AuthenticationError("Refresh token has been revoked or expired", code="REVOKED_TOKEN")

        # Revoke old refresh token (Token Rotation)
        await self.user_repo.revoke_refresh_token(saved_token, datetime.now(timezone.utc))

        user = await self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User is no longer active", code="USER_INACTIVE")

        # Generate new token pair
        token_data = {"sub": user.id, "org_id": user.organization_id, "role": user.role.value}
        new_access = create_access_token(token_data)
        new_refresh = create_refresh_token(token_data)

        refresh_exp = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        new_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_refresh),
            expires_at=refresh_exp
        )
        await self.user_repo.save_refresh_token(new_token_record)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    async def logout(self, refresh_token_str: str) -> None:
        tok_hash = hash_token(refresh_token_str)
        saved_token = await self.user_repo.get_refresh_token(tok_hash)
        if saved_token:
            await self.user_repo.revoke_refresh_token(saved_token, datetime.now(timezone.utc))
