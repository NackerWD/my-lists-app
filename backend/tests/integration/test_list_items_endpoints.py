"""Tests d'integració per als endpoints d'ítems de llista.
La BD és real (PostgreSQL via NullPool). Supabase i get_current_user estan
mocked via el fixture `client` del conftest.

Els usuaris de test existeixen a la BD gràcies a la migració 0003_seed_test_users
(només activa quan ENVIRONMENT=test).
"""
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.list import List
from app.models.list_item import ListItem
from app.models.list_member import ListMember

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


async def _setup_list(db: AsyncSession, title: str = "Test List") -> uuid.UUID:
    from sqlalchemy import text
    await db.execute(text("""
        INSERT INTO users (id, email, display_name, created_at)
        VALUES ('550e8400-e29b-41d4-a716-446655440000', 'test@example.com', 'Test User', NOW())
        ON CONFLICT (id) DO NOTHING
    """))
    now = datetime.now(timezone.utc)
    list_id = uuid.uuid4()
    lst = List(id=list_id, owner_id=MOCK_USER_ID, title=title, updated_at=now, created_at=now)
    db.add(lst)
    member = ListMember(
        id=uuid.uuid4(),
        list_id=list_id,
        user_id=MOCK_USER_ID,
        role="owner",
        joined_at=now,
    )
    db.add(member)
    await db.commit()
    await db.expunge_all()  # allibera objectes ORM per evitar connexions obertes al teardown
    return list_id


async def _insert_item(
    db: AsyncSession,
    list_id: uuid.UUID,
    content: str = "Ítem de test",
    position: int = 0,
) -> uuid.UUID:
    now = datetime.now(timezone.utc)
    item_id = uuid.uuid4()
    item = ListItem(
        id=item_id,
        list_id=list_id,
        created_by=MOCK_USER_ID,
        content=content,
        position=position,
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    await db.commit()
    await db.expunge_all()  # allibera objectes ORM per evitar connexions obertes al teardown
    return item_id


class TestGetItems:
    async def test_get_items_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        list_id = await _setup_list(db_session)
        response = await client.get(f"/api/v1/lists/{list_id}/items")
        assert response.status_code == 200
        assert response.json() == []


class TestCreateItem:
    async def test_create_item(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        list_id = await _setup_list(db_session)
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
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        list_id = await _setup_list(db_session)
        response = await client.post(f"/api/v1/lists/{list_id}/items", json={})
        assert response.status_code == 422


class TestUpdateItem:
    async def test_update_item_check(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        list_id = await _setup_list(db_session)
        item_id = await _insert_item(db_session, list_id, "Tasca pendent")
        response = await client.patch(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            json={"is_checked": True},
        )
        assert response.status_code == 200
        assert response.json()["is_checked"] is True

    async def test_update_item_priority(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        list_id = await _setup_list(db_session)
        item_id = await _insert_item(db_session, list_id, "Tasca important")
        response = await client.patch(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            json={"priority": "high"},
        )
        assert response.status_code == 200
        assert response.json()["priority"] == "high"


class TestDeleteItem:
    async def test_delete_item(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        list_id = await _setup_list(db_session)
        item_id = await _insert_item(db_session, list_id)
        response = await client.delete(f"/api/v1/lists/{list_id}/items/{item_id}")
        assert response.status_code == 200
        assert response.json() == {"deleted": True}


class TestItemsOrdering:
    async def test_items_ordered_by_position(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        list_id = await _setup_list(db_session)
        # Inserir en ordre invers perquè el GET els retorni ordenats per position
        await _insert_item(db_session, list_id, "Tercer", position=2)
        await _insert_item(db_session, list_id, "Primer", position=0)
        await _insert_item(db_session, list_id, "Segon", position=1)

        response = await client.get(f"/api/v1/lists/{list_id}/items")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 3
        assert items[0]["content"] == "Primer"
        assert items[1]["content"] == "Segon"
        assert items[2]["content"] == "Tercer"
