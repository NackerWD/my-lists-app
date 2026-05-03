"""Tests unitaris GET /list-types."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.models.list_type import ListType


def _exec_scalars_all(items: list):
    r = MagicMock()
    inner = MagicMock()
    inner.all.return_value = items
    r.scalars.return_value = inner
    return r


@pytest.mark.asyncio
async def test_get_list_types(client_full_bypass: tuple[AsyncClient, AsyncMock]) -> None:
    client, mock_db = client_full_bypass
    tid = uuid.uuid4()
    row = ListType(id=tid, slug="shopping", label="Compres", icon="shopping-cart", is_active=True)
    mock_db.execute = AsyncMock(return_value=_exec_scalars_all([row]))

    r = await client.get("/api/v1/list-types/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["slug"] == "shopping"
    assert data[0]["label"] == "Compres"
    assert data[0]["icon"] == "shopping-cart"
