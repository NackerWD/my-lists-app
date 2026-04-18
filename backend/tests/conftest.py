import asyncio
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from app.core.database import Base

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db",
)


@pytest.fixture(scope="session")
def event_loop():
    """Un sol event loop per a tota la sessió — evita 'attached to a different loop'."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO users (id, email, display_name, created_at)
            VALUES
                ('550e8400-e29b-41d4-a716-446655440000', 'test@example.com', 'Test User', NOW()),
                ('650e8400-e29b-41d4-a716-446655440001', 'other@example.com', 'Other User', NOW())
            ON CONFLICT (id) DO NOTHING
        """))
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Sessió nova per cada test. Fa rollback al final per aïllar els tests."""
    async_session = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@dataclass
class MockUser:
    """Usuari mockat com a dataclass real per evitar conflictes amb SQLAlchemy i FastAPI."""

    id: uuid.UUID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    email: str = "test@example.com"
    display_name: Optional[str] = "Test User"
    avatar_url: Optional[str] = None
    created_at: datetime = datetime(2024, 1, 1, tzinfo=timezone.utc)
    last_seen_at: Optional[datetime] = None


@pytest.fixture
def mock_current_user() -> MockUser:
    return MockUser()


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    mock_sess = MagicMock()
    mock_sess.access_token = "fake-access-token"
    mock_sess.refresh_token = "fake-refresh-token"
    mock_sess.expires_in = 900
    mock_user_data = MagicMock()
    mock_user_data.id = "550e8400-e29b-41d4-a716-446655440000"
    mock_user_data.email = "test@example.com"
    client.auth.sign_up.return_value = MagicMock(user=mock_user_data, session=mock_sess)
    client.auth.sign_in_with_password.return_value = MagicMock(
        user=mock_user_data, session=mock_sess
    )
    client.auth.sign_out.return_value = None
    client.auth.refresh_session.return_value = MagicMock(session=mock_sess)
    client.auth.get_user.return_value = MagicMock(user=mock_user_data)
    client.auth.admin = MagicMock()
    client.auth.admin.sign_out = MagicMock(return_value=None)
    return client


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_current_user: MockUser):
    from app.core.database import get_db
    from app.core.security import get_current_user
    from main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
