"""Integration tests for list member endpoints."""
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from tests.integration.db_asserts import (
    assert_list_and_membership,
    assert_list_members_count_at_least,
    assert_members_join_users_possible,
)

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")
THIRD_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


async def _setup_list(
    engine: AsyncEngine,
    owner_id: str = "550e8400-e29b-41d4-a716-446655440000",
) -> uuid.UUID:
    list_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO users (id, email, display_name, created_at)
            VALUES
                ('550e8400-e29b-41d4-a716-446655440000', 'test@example.com', 'Test User', NOW()),
                ('650e8400-e29b-41d4-a716-446655440001', 'other@example.com', 'Other User', NOW())
            ON CONFLICT (id) DO NOTHING
        """))
        await conn.execute(text("""
            INSERT INTO lists (id, owner_id, title, is_archived, created_at, updated_at)
            VALUES (:id, :owner_id, 'Test List', false, :now, :now)
        """), {"id": str(list_id), "owner_id": owner_id, "now": now})
        await conn.execute(text("""
            INSERT INTO list_members (id, list_id, user_id, role, joined_at)
            VALUES (:id, :list_id, :user_id, 'owner', :now)
        """), {"id": str(uuid.uuid4()), "list_id": str(list_id), "user_id": owner_id, "now": now})
    return list_id


async def _ensure_third_user(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO users (id, email, display_name, created_at)
            VALUES (:id, 'third@example.com', 'Third User', NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(THIRD_USER_ID)})


async def _add_member(
    engine: AsyncEngine,
    list_id: uuid.UUID,
    user_id: str,
    role: str = "editor",
) -> None:
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO list_members (id, list_id, user_id, role, joined_at)
            VALUES (:id, :list_id, :user_id, :role, :now)
            ON CONFLICT (list_id, user_id) DO NOTHING
        """), {"id": str(uuid.uuid4()), "list_id": str(list_id), "user_id": user_id, "role": role, "now": now})


class TestGetMembers:
    async def test_get_members(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        list_id = await _setup_list(test_engine)
        await _add_member(test_engine, list_id, str(OTHER_USER_ID), "editor")
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        await assert_list_members_count_at_least(db_session, list_id, 2)
        await assert_members_join_users_possible(db_session, list_id, 2)

        response = await client_owner.get(f"/api/v1/lists/{list_id}/members")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        roles = {m["role"] for m in data}
        assert "owner" in roles
        assert "editor" in roles

    async def test_get_members_includes_user_info(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        list_id = await _setup_list(test_engine)
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        await assert_members_join_users_possible(db_session, list_id, 1)

        response = await client_owner.get(f"/api/v1/lists/{list_id}/members")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        member = data[0]
        assert "email" in member
        assert "display_name" in member
        assert "role" in member

    async def test_get_members_not_member(self, client: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(
            test_engine,
            owner_id="650e8400-e29b-41d4-a716-446655440001",
        )
        response = await client.get(f"/api/v1/lists/{list_id}/members")
        assert response.status_code == 403

    async def test_get_members_three_users(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        await _ensure_third_user(test_engine)
        list_id = await _setup_list(test_engine)
        await _add_member(test_engine, list_id, str(OTHER_USER_ID), "editor")
        await _add_member(test_engine, list_id, str(THIRD_USER_ID), "editor")
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        await assert_list_members_count_at_least(db_session, list_id, 3)
        await assert_members_join_users_possible(db_session, list_id, 3)

        response = await client_owner.get(f"/api/v1/lists/{list_id}/members")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for m in data:
            assert "email" in m
            assert "display_name" in m
            assert "role" in m
            assert m["user_id"] in (
                str(MOCK_USER_ID),
                str(OTHER_USER_ID),
                str(THIRD_USER_ID),
            )


class TestRemoveMember:
    async def test_remove_member(self, client_owner: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(test_engine)
        await _add_member(test_engine, list_id, str(OTHER_USER_ID), "editor")

        response = await client_owner.delete(f"/api/v1/lists/{list_id}/members/{OTHER_USER_ID}")
        assert response.status_code == 200
        assert response.json() == {"deleted": True}

        after = await client_owner.get(f"/api/v1/lists/{list_id}/members")
        assert after.status_code == 200
        ids_after = {m["user_id"] for m in after.json()}
        assert str(OTHER_USER_ID) not in ids_after
        assert str(MOCK_USER_ID) in ids_after

    async def test_remove_owner(self, client: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(test_engine)

        response = await client.delete(f"/api/v1/lists/{list_id}/members/{MOCK_USER_ID}")
        assert response.status_code == 403

    async def test_remove_non_member(self, client_owner: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(test_engine)
        random_user = uuid.uuid4()

        response = await client_owner.delete(f"/api/v1/lists/{list_id}/members/{random_user}")
        assert response.status_code == 404

    async def test_remove_member_not_owner(self, client: AsyncClient, test_engine: AsyncEngine) -> None:
        # MOCK_USER_ID is only a viewer — cannot remove members
        list_id = await _setup_list(
            test_engine,
            owner_id="650e8400-e29b-41d4-a716-446655440001",
        )
        await _add_member(test_engine, list_id, str(MOCK_USER_ID), "viewer")

        response = await client.delete(f"/api/v1/lists/{list_id}/members/{OTHER_USER_ID}")
        assert response.status_code == 403
