"""Fixtures compartits per tests unitaris (p. ex. routers de llistes amb AsyncSession mockat)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import get_current_user, require_list_role
from app.models.list import List
from app.models.list_invitation import ListInvitation
from app.models.list_item import ListItem
from main import app

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.fixture
def mock_user() -> MagicMock:
    user = MagicMock()
    user.id = MOCK_USER_ID
    user.email = "test@example.com"
    user.display_name = "Test User"
    return user


async def _refresh_orm_defaults(obj: object) -> None:
    """Simula ``refresh`` posant camps que Pydantic espera des de ``model_validate``."""
    t = datetime.now(timezone.utc)
    if isinstance(obj, List):
        if getattr(obj, "created_at", None) is None:
            obj.created_at = t
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = t
        if getattr(obj, "is_archived", None) is None:
            obj.is_archived = False
    elif isinstance(obj, ListItem):
        if getattr(obj, "created_at", None) is None:
            obj.created_at = t
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = t
        if getattr(obj, "is_checked", None) is None:
            obj.is_checked = False
    elif isinstance(obj, ListInvitation):
        if getattr(obj, "created_at", None) is None:
            obj.created_at = t


@pytest_asyncio.fixture
async def client_full_bypass(mock_user: MagicMock):
    """Client HTTP amb auth i require_list_role bypassats i ``get_db`` -> AsyncMock."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock(side_effect=_refresh_orm_defaults)
    mock_db.delete = AsyncMock()

    async def override_get_current_user() -> MagicMock:
        return mock_user

    async def override_get_db():
        yield mock_db

    async def override_role(list_id: uuid.UUID) -> MagicMock:  # noqa: ARG001
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_list_role("owner")] = override_role
    app.dependency_overrides[require_list_role("editor")] = override_role
    app.dependency_overrides[require_list_role("viewer")] = override_role

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, mock_db

    app.dependency_overrides.clear()
