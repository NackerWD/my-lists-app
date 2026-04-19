"""Tests unitaris d'ítems, membres i invitacions amb AsyncSession mockat."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.models.list import List
from app.models.list_item import ListItem
from app.models.list_member import ListMember
from app.models.user import User

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_list(list_id: uuid.UUID) -> List:
    t = _now()
    return List(
        id=list_id,
        owner_id=MOCK_USER_ID,
        title="L",
        description=None,
        is_archived=False,
        list_type_id=None,
        created_at=t,
        updated_at=t,
    )


def _make_member(list_id: uuid.UUID, user_id: uuid.UUID, role: str = "owner") -> ListMember:
    return ListMember(
        id=uuid.uuid4(),
        list_id=list_id,
        user_id=user_id,
        role=role,
        joined_at=_now(),
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


def _exec_all_rows(rows: list):
    r = MagicMock()
    r.all.return_value = rows
    return r


class TestGetItemsUnit:
    async def test_get_items_empty(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        lst = _make_list(lid)
        mem = _make_member(lid, MOCK_USER_ID)
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalar_one_or_none(lst),
                _exec_scalar_one_or_none(mem),
                _exec_scalars_all([]),
            ]
        )

        r = await client.get(f"/api/v1/lists/{lid}/items")
        assert r.status_code == 200
        assert r.json() == []


class TestCreateItemUnit:
    @patch("app.api.v1.endpoints.list_items.asyncio.create_task", MagicMock())
    async def test_create_item(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        lst = _make_list(lid)
        mem = _make_member(lid, MOCK_USER_ID)
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalar_one_or_none(lst),
                _exec_scalar_one_or_none(mem),
                _exec_scalar(None),
                _exec_scalar_one_or_none(lst),
            ]
        )

        r = await client.post(
            f"/api/v1/lists/{lid}/items",
            json={"content": "Comprar pa"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["content"] == "Comprar pa"
        assert body["position"] == 0
        mock_db.add.assert_called()
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()


class TestUpdateDeleteItemUnit:
    @patch("app.api.v1.endpoints.list_items.asyncio.create_task", MagicMock())
    async def test_update_item(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        iid = uuid.uuid4()
        t = _now()
        item = ListItem(
            id=iid,
            list_id=lid,
            created_by=MOCK_USER_ID,
            content="Antic",
            is_checked=False,
            position=0,
            due_date=None,
            priority=None,
            remind_at=None,
            metadata_=None,
            created_at=t,
            updated_at=t,
        )
        lst = _make_list(lid)
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalar_one_or_none(item),
                _exec_scalar_one_or_none(lst),
            ]
        )

        r = await client.patch(
            f"/api/v1/lists/{lid}/items/{iid}",
            json={"content": "Nou", "is_checked": True, "priority": "high"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["content"] == "Nou"
        assert body["is_checked"] is True
        assert body["priority"] == "high"

    @patch("app.api.v1.endpoints.list_items.asyncio.create_task", MagicMock())
    async def test_delete_item(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        iid = uuid.uuid4()
        t = _now()
        item = ListItem(
            id=iid,
            list_id=lid,
            created_by=MOCK_USER_ID,
            content="X",
            is_checked=False,
            position=0,
            due_date=None,
            priority=None,
            remind_at=None,
            metadata_=None,
            created_at=t,
            updated_at=t,
        )
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(item))

        r = await client.delete(f"/api/v1/lists/{lid}/items/{iid}")
        assert r.status_code == 200
        assert r.json() == {"deleted": True}
        mock_db.delete.assert_awaited()


class TestGetMembersUnit:
    async def test_get_members(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        member_row = _make_member(lid, MOCK_USER_ID, role="owner")
        other_user = User(
            id=OTHER_USER_ID,
            email="other@example.com",
            display_name="Other",
            avatar_url=None,
            created_at=_now(),
            last_seen_at=None,
        )
        other_member = _make_member(lid, OTHER_USER_ID, role="editor")
        mock_db.execute = AsyncMock(
            side_effect=[
                _exec_scalar_one_or_none(member_row),
                _exec_all_rows([(other_member, other_user)]),
            ]
        )

        r = await client.get(f"/api/v1/lists/{lid}/members")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["email"] == "other@example.com"
        assert data[0]["role"] == "editor"


class TestRemoveMemberUnit:
    async def test_remove_member_editor(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        target = _make_member(lid, OTHER_USER_ID, role="editor")
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(target))

        r = await client.delete(f"/api/v1/lists/{lid}/members/{OTHER_USER_ID}")
        assert r.status_code == 200
        assert r.json() == {"deleted": True}
        mock_db.delete.assert_awaited()
        mock_db.commit.assert_awaited()


class TestInviteUnit:
    async def test_invite_list_not_found(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(None))

        r = await client.post(
            f"/api/v1/lists/{uuid.uuid4()}/invite",
            json={"email": "x@y.com", "role": "editor"},
        )
        assert r.status_code == 404

    async def test_invite_to_list(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        lid = uuid.uuid4()
        lst = _make_list(lid)
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(lst))

        r = await client.post(
            f"/api/v1/lists/{lid}/invite",
            json={"email": "convidat@example.com", "role": "editor"},
        )
        assert r.status_code == 201
        body = r.json()
        assert "invitation_id" in body
        assert "link" in body
        assert "/invite/" in body["link"]
        mock_db.add.assert_called()
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()
