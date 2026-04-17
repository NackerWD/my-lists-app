"""Tests d'integració per als endpoints de llistes.
La BD és real (PostgreSQL via NullPool). Supabase i get_current_user estan
mocked via el fixture `client` del conftest.
"""
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.list import List
from app.models.list_member import ListMember
from app.models.user import User

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")


async def _insert_user(db: AsyncSession, user_id: uuid.UUID, email: str) -> None:
    user = User(
        id=user_id,
        email=email,
        display_name=email.split("@")[0],
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)


async def _create_list_direct(
    db: AsyncSession,
    title: str = "Test List",
    owner_id: uuid.UUID = MOCK_USER_ID,
    member_id: uuid.UUID = MOCK_USER_ID,
    role: str = "owner",
) -> uuid.UUID:
    """Insereix una llista + membre directament a la BD. Retorna l'id de la llista."""
    list_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    lst = List(
        id=list_id,
        owner_id=owner_id,
        title=title,
        updated_at=now,
        created_at=now,
    )
    db.add(lst)
    member = ListMember(
        id=uuid.uuid4(),
        list_id=list_id,
        user_id=member_id,
        role=role,
        joined_at=now,
    )
    db.add(member)
    await db.commit()
    return list_id


class TestGetLists:
    async def test_get_lists_empty(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        await db_session.commit()
        response = await client.get("/api/v1/lists/")
        assert response.status_code == 200
        assert response.json() == []


class TestCreateList:
    async def test_create_list(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        await db_session.commit()
        response = await client.post("/api/v1/lists/", json={"title": "La meva llista"})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "La meva llista"
        assert data["member_count"] == 1

    async def test_create_list_invalid(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        await db_session.commit()
        response = await client.post("/api/v1/lists/", json={})
        assert response.status_code == 422


class TestGetListById:
    async def test_get_list_by_id(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        list_id = await _create_list_direct(db_session, title="Detall")
        response = await client.get(f"/api/v1/lists/{list_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Detall"
        assert str(data["id"]) == str(list_id)

    async def test_get_list_not_found(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        await db_session.commit()
        response = await client.get(f"/api/v1/lists/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_get_list_not_member(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        await _insert_user(db_session, OTHER_USER_ID, "other@example.com")
        # Crea llista sense afegir mock_current_user com a membre
        list_id = await _create_list_direct(
            db_session, owner_id=OTHER_USER_ID, member_id=OTHER_USER_ID, role="owner"
        )
        response = await client.get(f"/api/v1/lists/{list_id}")
        assert response.status_code == 403


class TestUpdateList:
    async def test_update_list(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        list_id = await _create_list_direct(db_session, title="Original")
        response = await client.patch(
            f"/api/v1/lists/{list_id}", json={"title": "Actualitzat"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Actualitzat"


class TestDeleteList:
    async def test_delete_list(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        list_id = await _create_list_direct(db_session)
        response = await client.delete(f"/api/v1/lists/{list_id}")
        assert response.status_code == 200
        assert response.json() == {"deleted": True}

    async def test_delete_list_not_owner(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _insert_user(db_session, MOCK_USER_ID, "test@example.com")
        await _insert_user(db_session, OTHER_USER_ID, "other@example.com")
        # Crea llista amb OTHER_USER com a owner; MOCK_USER és viewer
        list_id = await _create_list_direct(
            db_session,
            owner_id=OTHER_USER_ID,
            member_id=MOCK_USER_ID,
            role="viewer",
        )
        response = await client.delete(f"/api/v1/lists/{list_id}")
        assert response.status_code == 403
