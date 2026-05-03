"""Tests unitaris dels endpoints ``lists`` amb AsyncSession mockat (sense BD real)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.models.list import List

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


def _exec_all(rows: list):
    """Resultat de ``execute`` quan el codi crida ``.all()`` (p. ex. get_lists)."""
    r = MagicMock()
    r.all.return_value = rows
    return r


def _exec_row_one(mcnt: int, icnt: int):
    """Resultat de ``execute`` quan el codi crida ``.one()`` (subconsultes de counts)."""
    r = MagicMock()
    r.one.return_value = (mcnt, icnt)
    return r


def _exec_one_or_none(row_tuple):
    r = MagicMock()
    r.one_or_none.return_value = row_tuple
    return r


class TestGetListsUnit:
    async def test_get_lists_empty(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock(return_value=_exec_all([]))

        r = await client.get("/api/v1/lists/")
        assert r.status_code == 200
        assert r.json() == []
        mock_db.execute.assert_awaited_once()

    async def test_get_lists_one_list_counts(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lst = _make_list(title="Una")
        mock_db.execute = AsyncMock(return_value=_exec_all([(lst, None, None, 1, 0)]))

        r = await client.get("/api/v1/lists/")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["title"] == "Una"
        assert data[0]["member_count"] == 1
        assert data[0]["item_count"] == 0
        assert mock_db.execute.await_count == 1


class TestGetListByIdUnit:
    async def test_get_list_by_id_success(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        lst = _make_list(list_id=lid, title="Detall")
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_one_or_none((lst, None, None)),
                _exec_row_one(2, 3),
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
        mock_db.execute = AsyncMock(return_value=_exec_one_or_none(None))

        r = await client.get(f"/api/v1/lists/{uuid.uuid4()}")
        assert r.status_code == 404


class TestCreateListUnit:
    async def test_create_list(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock()

        r = await client.post("/api/v1/lists/", json={"title": "Nova"})
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "Nova"
        assert body["member_count"] == 1
        assert body["item_count"] == 0
        mock_db.add.assert_called()
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()
        mock_db.execute.assert_not_called()


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
                _exec_one_or_none((lst, None, None)),
                _exec_one_or_none((lst, None, None)),
                _exec_row_one(1, 0),
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
        mock_db.execute = AsyncMock(return_value=_exec_one_or_none((lst, None, None)))

        r = await client.delete(f"/api/v1/lists/{lid}")
        assert r.status_code == 200
        assert r.json() == {"deleted": True}
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_awaited()
