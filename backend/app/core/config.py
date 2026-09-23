from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "SupportIQ — AI Customer Support & Knowledge Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./supportiq.db"
    SYNC_DATABASE_URL: str = "sqlite:///./supportiq.db"
    POSTGRES_DB: str = "supportiq_db"
    POSTGRES_USER: str = "supportiq"
    POSTGRES_PASSWORD: str = "supportiq"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Redis & Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET: str = "supportiq-super-secret-jwt-key-2026-production-ready-998877"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ]

    # AI & Embedding Providers
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "gemini"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # RAG & Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    RETRIEVAL_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.45
    AUTO_ESCALATION_THRESHOLD: float = 0.60

    # Rate Limiting (requests per minute)
    RATE_LIMIT_UNAUTH: int = 20
    RATE_LIMIT_AUTH: int = 60
    RATE_LIMIT_AI: int = 10

    # Upload & Storage
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]

    # Refund Business Logic Config
    REFUND_WINDOW_DAYS: int = 30
    HIGH_VALUE_REFUND_THRESHOLD: float = 500.0

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
