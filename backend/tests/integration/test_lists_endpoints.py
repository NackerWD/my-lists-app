"""Tests d'integració per als endpoints de llistes.
La BD és real (PostgreSQL via NullPool). Supabase i get_current_user estan
mocked via els fixtures ``client`` / ``client_owner`` del conftest.

Els usuaris de test (MOCK_USER_ID i OTHER_USER_ID) existeixen a la BD gràcies
a la migració 0003_seed_test_users (només activa quan ENVIRONMENT=test).
"""
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from tests.integration.db_asserts import (
    assert_list_and_membership,
    assert_list_items_count,
    assert_list_members_count_at_least,
)

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")


async def _create_list_direct(
    engine: AsyncEngine,
    title: str = "Test List",
    owner_id: str | None = None,
    member_id: str | None = None,
    role: str = "owner",
    is_archived: bool = False,
) -> uuid.UUID:
    """Insereix llista + membre via engine.begin()."""
    if owner_id is None:
        owner_id = str(MOCK_USER_ID)
    if member_id is None:
        member_id = str(MOCK_USER_ID)
    list_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO users (id, email, display_name, created_at)
            VALUES
                (:mock_id, 'test@example.com', 'Test User', NOW()),
                (:other_id, 'other@example.com', 'Other User', NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"mock_id": str(MOCK_USER_ID), "other_id": str(OTHER_USER_ID)})
        await conn.execute(text("""
            INSERT INTO lists (id, owner_id, title, is_archived, created_at, updated_at)
            VALUES (:id, :owner_id, :title, :is_archived, :now, :now)
        """), {"id": str(list_id), "owner_id": owner_id, "title": title, "is_archived": is_archived, "now": now})
        await conn.execute(text("""
            INSERT INTO list_members (id, list_id, user_id, role, joined_at)
            VALUES (:id, :list_id, :member_id, :role, :now)
        """), {"id": str(uuid.uuid4()), "list_id": str(list_id), "member_id": member_id, "role": role, "now": now})
    return list_id


async def _add_member_and_items(engine: AsyncEngine, list_id: uuid.UUID) -> None:
    """Afegeix un segon membre i dos ítems per provar member_count / item_count."""
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO list_members (id, list_id, user_id, role, joined_at)
            VALUES (:id, :list_id, :other_id, 'editor', :now)
            ON CONFLICT (list_id, user_id) DO NOTHING
        """), {
            "id": str(uuid.uuid4()),
            "list_id": str(list_id),
            "other_id": str(OTHER_USER_ID),
            "now": now,
        })
        for pos, content in enumerate(("Un", "Dos")):
            await conn.execute(text("""
                INSERT INTO list_items (id, list_id, created_by, content, is_checked, position, created_at, updated_at)
                VALUES (:id, :list_id, :mock_id, :content, false, :pos, :now, :now)
            """), {
                "id": str(uuid.uuid4()),
                "list_id": str(list_id),
                "mock_id": str(MOCK_USER_ID),
                "content": content,
                "pos": pos,
                "now": now,
            })


class TestGetLists:
    async def test_get_lists_returns_array(self, client_owner: AsyncClient) -> None:
        """Comprova que el endpoint retorna 200 i una llista JSON.
        No s'assumeix que la BD estigui buida perquè tests anteriors poden
        haver commitejat llistes (NullPool no reverteix commits)."""
        response = await client_owner.get("/api/v1/lists/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_archived_lists(
        self, client_owner: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _create_list_direct(
            test_engine, title="Arxivada", is_archived=True
        )
        response = await client_owner.get("/api/v1/lists/")
        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert str(list_id) not in ids


class TestCreateList:
    async def test_create_list(self, client_owner: AsyncClient) -> None:
        response = await client_owner.post("/api/v1/lists/", json={"title": "La meva llista"})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "La meva llista"
        assert data["member_count"] == 1

    async def test_create_list_invalid(self, client_owner: AsyncClient) -> None:
        response = await client_owner.post("/api/v1/lists/", json={})
        assert response.status_code == 422


class TestGetListById:
    async def test_get_list_by_id(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        list_id = await _create_list_direct(test_engine, title="Detall")
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        response = await client_owner.get(f"/api/v1/lists/{list_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Detall"
        assert str(data["id"]) == str(list_id)

    async def test_get_list_not_found(self, client_owner: AsyncClient) -> None:
        response = await client_owner.get(f"/api/v1/lists/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_get_list_not_member(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _create_list_direct(
            test_engine,
            owner_id="650e8400-e29b-41d4-a716-446655440001",
            member_id="650e8400-e29b-41d4-a716-446655440001",
        )
        response = await client.get(f"/api/v1/lists/{list_id}")
        assert response.status_code == 403

    async def test_get_list_with_counts(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        list_id = await _create_list_direct(test_engine, title="Amb comptadors")
        await _add_member_and_items(test_engine, list_id)
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        await assert_list_members_count_at_least(db_session, list_id, 2)
        await assert_list_items_count(db_session, list_id, 2)
        response = await client_owner.get(f"/api/v1/lists/{list_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["member_count"] == 2
        assert data["item_count"] == 2


class TestUpdateList:
    async def test_update_list(
        self, client_owner: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _create_list_direct(test_engine, title="Original")
        response = await client_owner.patch(
            f"/api/v1/lists/{list_id}", json={"title": "Actualitzat"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Actualitzat"

    async def test_update_list_not_editor(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _create_list_direct(
            test_engine,
            owner_id="650e8400-e29b-41d4-a716-446655440001",
            member_id="550e8400-e29b-41d4-a716-446655440000",
            role="viewer",
        )
        response = await client.patch(
            f"/api/v1/lists/{list_id}", json={"title": "Hack"}
        )
        assert response.status_code == 403

    async def test_update_list_description_is_archived(
        self, client_owner: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _create_list_direct(test_engine, title="Títol inicial")
        response = await client_owner.patch(
            f"/api/v1/lists/{list_id}",
            json={
                "title": "Nou títol",
                "description": "Desc actualitzada",
                "is_archived": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Nou títol"
        assert data["description"] == "Desc actualitzada"
        assert data["is_archived"] is True


class TestDeleteList:
    async def test_delete_list(
        self, client_owner: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _create_list_direct(test_engine)
        response = await client_owner.delete(f"/api/v1/lists/{list_id}")
        assert response.status_code == 200
        assert response.json() == {"deleted": True}

    async def test_delete_list_not_owner(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _create_list_direct(
            test_engine,
            owner_id="650e8400-e29b-41d4-a716-446655440001",
            member_id="650e8400-e29b-41d4-a716-446655440001",
        )
        response = await client.delete(f"/api/v1/lists/{list_id}")
        assert response.status_code == 403
