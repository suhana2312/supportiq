from fastapi import APIRouter
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.conversations import router as conversations_router
from backend.app.api.v1.orders import router as orders_router
from backend.app.api.v1.refunds import router as refunds_router
from backend.app.api.v1.tickets import router as tickets_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.organization import router as organization_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(documents_router)
api_router.include_router(conversations_router)
api_router.include_router(orders_router)
api_router.include_router(refunds_router)
api_router.include_router(tickets_router)
api_router.include_router(analytics_router)
api_router.include_router(organization_router)
