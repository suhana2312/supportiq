from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import User
from backend.app.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, RefreshTokenRequest, TokenResponse, UserResponse
)
from backend.app.schemas.common import StandardResponse
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=StandardResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    tokens = await auth_service.register(req)
    return StandardResponse(data=tokens)

@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    tokens = await auth_service.login(req)
    return StandardResponse(data=tokens)

@router.post("/refresh", response_model=StandardResponse[TokenResponse])
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_token(req)
    return StandardResponse(data=tokens)

@router.post("/logout", response_model=StandardResponse[dict])
async def logout(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.logout(req.refresh_token)
    return StandardResponse(data={"message": "Successfully logged out"})

@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return StandardResponse(data=UserResponse.model_validate(current_user))
