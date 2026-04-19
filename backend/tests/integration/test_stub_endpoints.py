"""Tests d'integració per als endpoints stub que encara no estan implementats.
Lists i list_items han estat eliminats d'aquí — coberts per
test_lists_endpoints.py i test_list_items_endpoints.py.

Els stubs retornen 501 Not Implemented explícitament (no silenci 200/204).
"""
import uuid

from httpx import AsyncClient


class TestListMembersEndpoints:
    async def test_get_members(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/lists/{list_id}/members",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 501

    async def test_remove_member(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        member_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/lists/{list_id}/members/{member_id}",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 501


class TestListInvitationsEndpoints:
    async def test_invite_to_list(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/lists/{list_id}/invite",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )
        assert response.status_code == 501

    async def test_get_invitation(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/invitations/some-token-abc")
        assert response.status_code == 501

    async def test_accept_invitation(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/invitations/some-token-abc/accept",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 501
