"""Tests d'integració per als endpoints d'ítems de llista.
La BD és real (PostgreSQL via NullPool). Supabase i get_current_user estan
mocked via el fixture `client` del conftest.

Els usuaris de test existeixen a la BD gràcies a la migració 0003_seed_test_users
(només activa quan ENVIRONMENT=test).
"""
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")


async def _setup_list(
    engine: AsyncEngine,
    title: str = "Test List",
    member_role: str = "owner",
) -> uuid.UUID:
    """Insereix llista + membre via engine.begin() — independent de db_session.

    Si member_role != 'owner', OTHER_USER esdevé el propietari de la llista
    i MOCK_USER s'afegeix amb el rol indicat (cal coincidir amb el client mock).
    """
    list_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    owner_id = str(MOCK_USER_ID) if member_role == "owner" else str(OTHER_USER_ID)
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
            VALUES (:id, :owner_id, :title, false, :now, :now)
        """), {"id": str(list_id), "owner_id": owner_id, "title": title, "now": now})
        await conn.execute(text("""
            INSERT INTO list_members (id, list_id, user_id, role, joined_at)
            VALUES (:id, :list_id, :member_user_id, :role, :now)
        """), {
            "id": str(uuid.uuid4()),
            "list_id": str(list_id),
            "member_user_id": str(MOCK_USER_ID),
            "role": member_role,
            "now": now,
        })
    return list_id


async def _insert_item(
    engine: AsyncEngine,
    list_id: uuid.UUID,
    content: str = "Test Item",
    position: int = 0,
) -> uuid.UUID:
    """Insereix un ítem via engine.begin() — independent de db_session."""
    item_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO list_items (id, list_id, created_by, content, is_checked, position, created_at, updated_at)
            VALUES (:id, :list_id, :created_by, :content, false, :position, :now, :now)
        """), {
            "id": str(item_id),
            "list_id": str(list_id),
            "created_by": str(MOCK_USER_ID),
            "content": content,
            "position": position,
            "now": now,
        })
    return item_id


async def _list_owned_only_by_other(engine: AsyncEngine) -> uuid.UUID:
    """Llista on MOCK_USER_ID no és membre: només OTHER com a owner.

    No afegir fila list_members per MOCK_USER_ID o test_get_items_not_member
    deixaria de comprovar el 403 per no-membre.
    """
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
            VALUES (:id, :other_id, 'Alien List', false, :now, :now)
        """), {"id": str(list_id), "other_id": str(OTHER_USER_ID), "now": now})
        await conn.execute(text("""
            INSERT INTO list_members (id, list_id, user_id, role, joined_at)
            VALUES (:id, :list_id, :other_id, 'owner', :now)
        """), {"id": str(uuid.uuid4()), "list_id": str(list_id), "other_id": str(OTHER_USER_ID), "now": now})
    return list_id


class TestGetItems:
    async def test_get_items_empty(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        response = await client.get(f"/api/v1/lists/{list_id}/items")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_items_list_not_found(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        missing = uuid.uuid4()
        response = await client.get(f"/api/v1/lists/{missing}/items")
        assert response.status_code == 404

    async def test_get_items_not_member(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _list_owned_only_by_other(test_engine)
        response = await client.get(f"/api/v1/lists/{list_id}/items")
        assert response.status_code == 403


class TestCreateItem:
    async def test_create_item(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        response = await client.post(
            f"/api/v1/lists/{list_id}/items",
            json={"content": "Comprar llet"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Comprar llet"
        assert data["is_checked"] is False
        assert "id" in data

    async def test_create_item_invalid(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        response = await client.post(f"/api/v1/lists/{list_id}/items", json={})
        assert response.status_code == 422

    async def test_create_item_position_auto(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        r1 = await client.post(
            f"/api/v1/lists/{list_id}/items", json={"content": "Primer"}
        )
        assert r1.status_code == 201
        assert r1.json()["position"] == 0
        r2 = await client.post(
            f"/api/v1/lists/{list_id}/items", json={"content": "Segon"}
        )
        assert r2.status_code == 201
        assert r2.json()["position"] == 1

    async def test_create_item_list_not_found(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        missing = uuid.uuid4()
        response = await client.post(
            f"/api/v1/lists/{missing}/items",
            json={"content": "Orfe"},
        )
        assert response.status_code == 404


class TestUpdateItem:
    async def test_update_item_check(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        item_id = await _insert_item(test_engine, list_id, "Tasca pendent")
        response = await client.patch(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            json={"is_checked": True},
        )
        assert response.status_code == 200
        assert response.json()["is_checked"] is True

    async def test_update_item_priority(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        item_id = await _insert_item(test_engine, list_id, "Tasca important")
        response = await client.patch(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            json={"priority": "high"},
        )
        assert response.status_code == 200
        assert response.json()["priority"] == "high"

    async def test_update_item_not_editor(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine, member_role="viewer")
        item_id = await _insert_item(test_engine, list_id, "Tasca")
        response = await client.patch(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            json={"is_checked": True},
        )
        assert response.status_code == 403

    async def test_update_item_wrong_list_id(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_a = await _setup_list(test_engine, title="A")
        list_b = await _setup_list(test_engine, title="B")
        item_id = await _insert_item(test_engine, list_a, "Només a A")
        response = await client.patch(
            f"/api/v1/lists/{list_b}/items/{item_id}",
            json={"content": "Hack"},
        )
        assert response.status_code == 404

    async def test_update_item_multiple_fields(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        item_id = await _insert_item(test_engine, list_id, "Original")
        due = "2026-06-15T12:00:00+00:00"
        remind = "2026-06-16T09:00:00+00:00"
        response = await client.patch(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            json={
                "content": "Actualitzat",
                "position": 5,
                "due_date": due,
                "remind_at": remind,
                "priority": "low",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Actualitzat"
        assert data["position"] == 5
        assert data["priority"] == "low"


class TestDeleteItem:
    async def test_delete_item(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        item_id = await _insert_item(test_engine, list_id)
        response = await client.delete(f"/api/v1/lists/{list_id}/items/{item_id}")
        assert response.status_code == 200
        assert response.json() == {"deleted": True}

    async def test_delete_item_not_found(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        response = await client.delete(
            f"/api/v1/lists/{list_id}/items/{uuid.uuid4()}"
        )
        assert response.status_code == 404

    async def test_delete_item_viewer_forbidden(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine, member_role="viewer")
        item_id = await _insert_item(test_engine, list_id, "Només lectura")
        response = await client.delete(
            f"/api/v1/lists/{list_id}/items/{item_id}"
        )
        assert response.status_code == 403


class TestItemsOrdering:
    async def test_items_ordered_by_position(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(test_engine)
        # Inserir en ordre invers perquè el GET els retorni ordenats per position
        await _insert_item(test_engine, list_id, "Tercer", position=2)
        await _insert_item(test_engine, list_id, "Primer", position=0)
        await _insert_item(test_engine, list_id, "Segon", position=1)

        response = await client.get(f"/api/v1/lists/{list_id}/items")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 3
        assert items[0]["content"] == "Primer"
        assert items[1]["content"] == "Segon"
        assert items[2]["content"] == "Tercer"
