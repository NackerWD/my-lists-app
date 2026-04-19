"""Tests unitaris dels endpoints ``lists`` amb AsyncSession mockat (sense BD real)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.list import List
from app.models.list_member import ListMember

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_list(list_id: uuid.UUID | None = None, title: str = "Llista") -> List:
    lid = list_id or uuid.uuid4()
    t = _now()
    return List(
        id=lid,
        owner_id=MOCK_USER_ID,
        title=title,
        description=None,
        is_archived=False,
        list_type_id=None,
        created_at=t,
        updated_at=t,
    )


def _exec_scalar_one_or_none(value):
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    r.scalar_one.return_value = value
    return r


def _exec_scalar(value):
    r = MagicMock()
    r.scalar.return_value = value
    return r


def _exec_scalars_all(items: list):
    r = MagicMock()
    inner = MagicMock()
    inner.all.return_value = items
    r.scalars.return_value = inner
    return r


class TestGetListsUnit:
    async def test_get_lists_empty(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock(return_value=_exec_scalars_all([]))

        r = await client.get("/api/v1/lists/")
        assert r.status_code == 200
        assert r.json() == []
        mock_db.execute.assert_awaited_once()

    async def test_get_lists_one_list_counts(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lst = _make_list(title="Una")
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalars_all([lst]),
                _exec_scalar(1),
                _exec_scalar(0),
            ]
        )

        r = await client.get("/api/v1/lists/")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["title"] == "Una"
        assert data[0]["member_count"] == 1
        assert data[0]["item_count"] == 0
        assert mock_db.execute.await_count == 3


class TestGetListByIdUnit:
    async def test_get_list_by_id_success(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        lst = _make_list(list_id=lid, title="Detall")
        member = ListMember(
            id=uuid.uuid4(),
            list_id=lid,
            user_id=MOCK_USER_ID,
            role="owner",
            joined_at=_now(),
        )
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalar_one_or_none(lst),
                _exec_scalar_one_or_none(member),
                _exec_scalar(2),
                _exec_scalar(3),
            ]
        )

        r = await client.get(f"/api/v1/lists/{lid}")
        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "Detall"
        assert body["member_count"] == 2
        assert body["item_count"] == 3

    async def test_get_list_by_id_not_found(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(None))

        r = await client.get(f"/api/v1/lists/{uuid.uuid4()}")
        assert r.status_code == 404

    async def test_get_list_by_id_not_member(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lst = _make_list()
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalar_one_or_none(lst),
                _exec_scalar_one_or_none(None),
            ]
        )

        r = await client.get(f"/api/v1/lists/{lst.id}")
        assert r.status_code == 403


class TestCreateListUnit:
    async def test_create_list(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock(side_effect=[_exec_scalar(1), _exec_scalar(0)])

        r = await client.post("/api/v1/lists/", json={"title": "Nova"})
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "Nova"
        assert body["member_count"] == 1
        assert body["item_count"] == 0
        mock_db.add.assert_called()
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()
        assert mock_db.execute.await_count == 2


class TestUpdateDeleteListUnit:
    @patch("app.api.v1.endpoints.lists.asyncio.create_task", MagicMock())
    async def test_update_list(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        lst = _make_list(list_id=lid, title="Antic")
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalar_one_or_none(lst),
                _exec_scalar(1),
                _exec_scalar(0),
            ]
        )

        r = await client.patch(
            f"/api/v1/lists/{lid}",
            json={"title": "Nou", "description": "D", "is_archived": True},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "Nou"
        assert body["description"] == "D"
        assert body["is_archived"] is True

    @patch("app.api.v1.endpoints.lists.asyncio.create_task", MagicMock())
    async def test_delete_list(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        lst = _make_list(list_id=lid)
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(lst))

        r = await client.delete(f"/api/v1/lists/{lid}")
        assert r.status_code == 200
        assert r.json() == {"deleted": True}
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_awaited()
