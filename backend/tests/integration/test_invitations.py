"""Integration tests for list invitation endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from tests.integration.db_asserts import assert_list_and_membership

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")


async def _setup_list(
    engine: AsyncEngine,
    owner_id: str = str(MOCK_USER_ID),
    member_id: str = str(MOCK_USER_ID),
    role: str = "owner",
) -> uuid.UUID:
    """Crea llista + un membre. El client d'integració és sempre MOCK_USER_ID.

    POST /lists/{id}/invite exigeix require_list_role("editor"): cal una fila
    list_members per MOCK_USER_ID amb rol >= editor (owner inclòs).
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
            VALUES (:id, :owner_id, 'Test List', false, :now, :now)
        """), {"id": str(list_id), "owner_id": owner_id, "now": now})
        await conn.execute(text("""
            INSERT INTO list_members (id, list_id, user_id, role, joined_at)
            VALUES (:id, :list_id, :user_id, :role, :now)
        """), {"id": str(uuid.uuid4()), "list_id": str(list_id), "user_id": member_id, "role": role, "now": now})
    return list_id


async def _insert_invitation(
    engine: AsyncEngine,
    list_id: uuid.UUID,
    token: str,
    role: str = "editor",
    invited_by: str = str(OTHER_USER_ID),
    expires_at: datetime | None = None,
    status: str = "pending",
) -> None:
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO list_invitations (id, list_id, invited_by, email, token, role, status, expires_at, created_at)
            VALUES (:id, :list_id, :invited_by, :email, :token, :role, :status, :expires_at, NOW())
        """), {
            "id": str(uuid.uuid4()),
            "list_id": str(list_id),
            "invited_by": invited_by,
            "email": "invite@example.com",
            "token": token,
            "role": role,
            "status": status,
            "expires_at": expires_at,
        })


class TestInviteMember:
    async def test_invite_member(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        list_id = await _setup_list(test_engine)
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        response = await client_owner.post(
            f"/api/v1/lists/{list_id}/invite",
            json={"email": "newmember@example.com", "role": "editor"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "invitation_id" in data
        assert "link" in data
        assert "/invite/" in data["link"]

    async def test_invite_member_invalid_role(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        list_id = await _setup_list(test_engine)
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        response = await client_owner.post(
            f"/api/v1/lists/{list_id}/invite",
            json={"email": "newmember@example.com", "role": "owner"},
        )
        assert response.status_code == 422

    async def test_invite_member_not_list_member(self, client: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(
            test_engine,
            owner_id=str(OTHER_USER_ID),
            member_id=str(OTHER_USER_ID),
        )
        response = await client.post(
            f"/api/v1/lists/{list_id}/invite",
            json={"email": "someone@example.com", "role": "viewer"},
        )
        assert response.status_code == 403

    async def test_invite_member_viewer_role(
        self,
        client_owner: AsyncClient,
        test_engine: AsyncEngine,
        db_session: AsyncSession,
    ) -> None:
        list_id = await _setup_list(test_engine)
        await assert_list_and_membership(db_session, list_id, MOCK_USER_ID)
        response = await client_owner.post(
            f"/api/v1/lists/{list_id}/invite",
            json={"email": "viewer@example.com", "role": "viewer"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "/invite/" in data["link"]
        assert "invitation_id" in data


class TestGetInvitation:
    async def test_get_invitation(self, client_owner: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(test_engine)
        token = str(uuid.uuid4())
        await _insert_invitation(test_engine, list_id, token)

        response = await client_owner.get(f"/api/v1/invitations/{token}")
        assert response.status_code == 200
        data = response.json()
        assert data["list_id"] == str(list_id)
        assert data["role"] == "editor"
        assert data["status"] == "pending"

    async def test_get_invitation_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/invitations/nonexistent-token")
        assert response.status_code == 404

    async def test_invitation_expired(self, client: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(test_engine)
        token = str(uuid.uuid4())
        past = datetime.now(timezone.utc) - timedelta(days=8)
        await _insert_invitation(test_engine, list_id, token, expires_at=past)

        response = await client.get(f"/api/v1/invitations/{token}")
        assert response.status_code == 410

    async def test_get_invitation_status_expired_field(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        """410 per status='expired' encara que expires_at sigui futur."""
        list_id = await _setup_list(test_engine)
        token = str(uuid.uuid4())
        future = datetime.now(timezone.utc) + timedelta(days=7)
        await _insert_invitation(
            test_engine, list_id, token, status="expired", expires_at=future
        )
        response = await client.get(f"/api/v1/invitations/{token}")
        assert response.status_code == 410


class TestAcceptInvitation:
    async def test_accept_invitation(self, client_owner: AsyncClient, test_engine: AsyncEngine) -> None:
        # List owned by OTHER_USER_ID — MOCK_USER_ID is NOT a member
        list_id = await _setup_list(
            test_engine,
            owner_id=str(OTHER_USER_ID),
            member_id=str(OTHER_USER_ID),
        )
        token = str(uuid.uuid4())
        await _insert_invitation(test_engine, list_id, token, role="editor")

        response = await client_owner.post(f"/api/v1/invitations/{token}/accept")
        assert response.status_code == 200
        data = response.json()
        assert data["list_id"] == str(list_id)
        assert data["role"] == "editor"

    async def test_duplicate_member(self, client: AsyncClient, test_engine: AsyncEngine) -> None:
        # MOCK_USER_ID is already owner of this list
        list_id = await _setup_list(test_engine)
        token = str(uuid.uuid4())
        await _insert_invitation(test_engine, list_id, token)

        response = await client.post(f"/api/v1/invitations/{token}/accept")
        assert response.status_code == 409

    async def test_accept_expired_invitation(self, client: AsyncClient, test_engine: AsyncEngine) -> None:
        list_id = await _setup_list(
            test_engine,
            owner_id=str(OTHER_USER_ID),
            member_id=str(OTHER_USER_ID),
        )
        token = str(uuid.uuid4())
        past = datetime.now(timezone.utc) - timedelta(days=8)
        await _insert_invitation(test_engine, list_id, token, expires_at=past)

        response = await client.post(f"/api/v1/invitations/{token}/accept")
        assert response.status_code == 410

    async def test_accept_invitation_not_found(self, client: AsyncClient) -> None:
        response = await client.post(
            f"/api/v1/invitations/{uuid.uuid4()}/accept"
        )
        assert response.status_code == 404

    async def test_accept_invitation_already_accepted_status(
        self, client: AsyncClient, test_engine: AsyncEngine
    ) -> None:
        list_id = await _setup_list(
            test_engine,
            owner_id=str(OTHER_USER_ID),
            member_id=str(OTHER_USER_ID),
        )
        token = str(uuid.uuid4())
        future = datetime.now(timezone.utc) + timedelta(days=7)
        await _insert_invitation(
            test_engine, list_id, token, status="accepted", expires_at=future
        )
        response = await client.post(f"/api/v1/invitations/{token}/accept")
        assert response.status_code == 410
