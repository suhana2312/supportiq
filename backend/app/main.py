from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, LoggingMiddleware
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.rate_limiter import check_rate_limit
from backend.app.db.database import init_db, AsyncSessionLocal
from backend.app.api.v1.router import api_router

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SupportIQ application...")
    await init_db()
    yield
    logger.info("Shutting down SupportIQ application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Multi-Tenant AI Customer Support Platform with RAG, LangGraph Agent, and Deterministic Operational Tools.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Structured Request Logging Middleware
app.add_middleware(LoggingMiddleware)

# 3. Centralized Exception Handlers
register_exception_handlers(app)

# 4. Global Rate Limiter Hook
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Only enforce on /api/ routes, exclude static or health docs
    if request.url.path.startswith(settings.API_V1_STR):
        await check_rate_limit(request)
    return await call_next(request)

# 5. Health & Observability Endpoints
@app.get("/health", tags=["Observability"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Observability"])
async def health_check():
    return {"status": "healthy", "service": "supportiq", "version": settings.VERSION}

@app.get("/ready", tags=["Observability"])
@app.get(f"{settings.API_V1_STR}/ready", tags=["Observability"])
async def readiness_check():
    # Verify DB connectivity
    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.error(f"Readiness check failed DB probe: {str(e)}")

    if not db_ok:
        return {"status": "not_ready", "database": "unavailable"}
    return {"status": "ready", "database": "connected"}

# 6. Mount API v1 Routes
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
