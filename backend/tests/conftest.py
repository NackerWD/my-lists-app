import os
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base  # Base definida a database.py, no a models

# Al CI: postgresql+asyncpg://test_user:test_password@localhost:5432/test_db
# En local: definir DATABASE_URL a l'entorn o usar els defaults del .env
TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db",
)


@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_supabase():
    """Mock del client Supabase per als tests que patchegen asyncio.to_thread."""
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


@pytest.fixture
def mock_current_user():
    """Usuari mockat per als tests que necessiten autenticació."""
    user = MagicMock()
    user.id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.avatar_url = None
    user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.last_seen_at = None
    return user


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_current_user: MagicMock):
    from main import app  # backend/main.py, no app.main
    from app.core.database import get_db
    from app.core.security import get_current_user

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
