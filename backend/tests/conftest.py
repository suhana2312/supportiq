import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.core.config import settings
from backend.app.db.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Organization, User
from backend.app.models.enums import UserRole
from backend.app.core.security import hash_password

TEST_DB_FILE = Path(__file__).parent / "test_db.sqlite"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def seeded_org_and_users():
    async with TestSessionLocal() as session:
        unique_suffix = os.urandom(3).hex()
        org1 = Organization(name="Org One", slug=f"org-one-{unique_suffix}")
        org2 = Organization(name="Org Two", slug=f"org-two-{unique_suffix}")
        session.add_all([org1, org2])
        await session.commit()
        await session.refresh(org1)
        await session.refresh(org2)

        admin1 = User(
            organization_id=org1.id,
            name="Admin Org 1",
            email=f"admin1_{unique_suffix}@test.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.ORGANIZATION_ADMIN,
            is_active=True
        )
        customer1 = User(
            organization_id=org1.id,
            name="Customer Org 1",
            email=f"cust1_{unique_suffix}@test.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.CUSTOMER,
            is_active=True
        )
        customer2 = User(
            organization_id=org2.id,
            name="Customer Org 2",
            email=f"cust2_{unique_suffix}@test.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.CUSTOMER,
            is_active=True
        )
        session.add_all([admin1, customer1, customer2])
        await session.commit()
        await session.refresh(admin1)
        await session.refresh(customer1)
        await session.refresh(customer2)

        return {
            "org1": org1,
            "org2": org2,
            "admin1": admin1,
            "customer1": customer1,
            "customer2": customer2
        }
