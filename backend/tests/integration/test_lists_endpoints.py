"""Tests d'integració per als endpoints de llistes.
La BD és real (PostgreSQL via NullPool). Supabase i get_current_user estan
mocked via el fixture `client` del conftest.

Nota: les insercions usen ON CONFLICT DO NOTHING perquè, amb NullPool, els
commits dins dels tests no es reverteixen entre tests (no hi ha savepoints).
"""
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.list import List
from app.models.list_member import ListMember

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")


async def _create_list_direct(
    db: AsyncSession,
    title: str = "Test List",
    owner_id: uuid.UUID = MOCK_USER_ID,
    member_id: uuid.UUID = MOCK_USER_ID,
    role: str = "owner",
) -> uuid.UUID:
    """Insereix una llista + membre directament a la BD. Retorna l'id de la llista.
    Assumeix que els usuaris (owner_id, member_id) ja existeixen a la BD."""
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
    async def test_get_lists_returns_array(self, client: AsyncClient, db_user) -> None:
        """Comprova que el endpoint retorna 200 i una llista JSON.
        No s'assumeix que la BD estigui buida perquè tests anteriors poden
        haver commitejat llistes (NullPool no reverteix commits)."""
        response = await client.get("/api/v1/lists/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestCreateList:
    async def test_create_list(self, client: AsyncClient, db_user) -> None:
        response = await client.post("/api/v1/lists/", json={"title": "La meva llista"})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "La meva llista"
        assert data["member_count"] == 1

    async def test_create_list_invalid(self, client: AsyncClient, db_user) -> None:
        response = await client.post("/api/v1/lists/", json={})
        assert response.status_code == 422


class TestGetListById:
    async def test_get_list_by_id(
        self, client: AsyncClient, db_session: AsyncSession, db_user
    ) -> None:
        list_id = await _create_list_direct(db_session, title="Detall")
        response = await client.get(f"/api/v1/lists/{list_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Detall"
        assert str(data["id"]) == str(list_id)

    async def test_get_list_not_found(self, client: AsyncClient, db_user) -> None:
        response = await client.get(f"/api/v1/lists/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_get_list_not_member(
        self, client: AsyncClient, db_session: AsyncSession, db_user
    ) -> None:
        # Crea llista sense afegir mock_current_user com a membre
        list_id = await _create_list_direct(
            db_session, owner_id=OTHER_USER_ID, member_id=OTHER_USER_ID, role="owner"
        )
        response = await client.get(f"/api/v1/lists/{list_id}")
        assert response.status_code == 403


class TestUpdateList:
    async def test_update_list(
        self, client: AsyncClient, db_session: AsyncSession, db_user
    ) -> None:
        list_id = await _create_list_direct(db_session, title="Original")
        response = await client.patch(
            f"/api/v1/lists/{list_id}", json={"title": "Actualitzat"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Actualitzat"


class TestDeleteList:
    async def test_delete_list(
        self, client: AsyncClient, db_session: AsyncSession, db_user
    ) -> None:
        list_id = await _create_list_direct(db_session)
        response = await client.delete(f"/api/v1/lists/{list_id}")
        assert response.status_code == 200
        assert response.json() == {"deleted": True}

    async def test_delete_list_not_owner(
        self, client: AsyncClient, db_session: AsyncSession, db_user
    ) -> None:
        # Crea llista amb OTHER_USER com a owner; MOCK_USER és viewer
        list_id = await _create_list_direct(
            db_session,
            owner_id=OTHER_USER_ID,
            member_id=MOCK_USER_ID,
            role="viewer",
        )
        response = await client.delete(f"/api/v1/lists/{list_id}")
        assert response.status_code == 403
