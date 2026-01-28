from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.llm import LLMService
from app.services.llm import llm_service as llm_service_dep

# Use in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for tests
# StaticPool is needed for in-memory SQLite to maintain the same connection
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session factory for tests
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def init_db() -> AsyncGenerator[None, None]:
    """Create tables before test and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(init_db: None) -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture that returns a SQLAlchemy session with a SAVEPOINT.
    This allows each test to run in a transaction that is rolled back.
    However, for simple in-memory tests with create_all/drop_all per test,
    we can just yield a session.
    """
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture for async HTTP client.
    Overrides the get_db dependency to use the test session.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
async def mock_llm_service() -> AsyncGenerator[AsyncMock, None]:
    """
    Fixture for mocked LLM service.
    Overrides the llm_service dependency.
    """
    mock = AsyncMock(spec=LLMService)
    mock.chat = AsyncMock()
    mock.close = AsyncMock()

    async def override_llm_service():
        yield mock

    app.dependency_overrides[llm_service_dep] = override_llm_service

    yield mock

    app.dependency_overrides.pop(llm_service_dep, None)


@pytest.fixture
async def auth_user(db_session: AsyncSession) -> dict:
    """
    Create an authenticated user and return user data with JWT token.
    Useful for testing protected endpoints.
    """
    from app.core.security import create_access_token
    from app.crud.crud_user import user as crud_user
    from app.schemas.user import UserCreate

    user_in = UserCreate(
        telegram_id=123456789,
        full_name="Test Auth User",
        username="testauth",
        email="testauth@example.com",
        password="testpassword123",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    access_token = create_access_token(subject=user.id)

    return {
        "user": user,
        "token": access_token,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture
async def auth_superuser(db_session: AsyncSession) -> dict:
    """
    Create an authenticated superuser and return user data with JWT token.
    Useful for testing endpoints that require superuser privileges.
    """
    from app.core.config import settings
    from app.core.security import create_access_token
    from app.crud.crud_user import user as crud_user
    from app.schemas.user import UserCreate

    user_in = UserCreate(
        telegram_id=987654321,
        full_name="Test Superuser",
        username="testsuperuser",
        email=settings.SUPERUSER_EMAIL,
        password="superpassword123",
        is_superuser=True,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    access_token = create_access_token(subject=user.id)

    return {
        "user": user,
        "token": access_token,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }
