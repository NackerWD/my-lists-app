import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import get_current_user
from main import app


@pytest.fixture
def mock_db():
    session = AsyncMock()
    # execute retorna un resultat configurat per defecte amb scalar_one_or_none = None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result
    # add és sync en SQLAlchemy — cal MagicMock, no AsyncMock
    session.add = MagicMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    client.auth.sign_up = MagicMock()
    client.auth.sign_in_with_password = MagicMock()
    client.auth.sign_out = MagicMock()
    client.auth.refresh_session = MagicMock()
    client.auth.get_user = MagicMock()
    client.auth.admin = MagicMock()
    client.auth.admin.sign_out = MagicMock()
    return client


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.avatar_url = None
    user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.last_seen_at = None
    return user


@pytest.fixture(autouse=True)
def override_dependencies(mock_db, mock_user):
    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
