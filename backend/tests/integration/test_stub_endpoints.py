"""Tests d'integració per als endpoints stub (TODO).
Comproven que els endpoints estan registrats i responen correctament
amb el mock de get_current_user ja configurat al conftest.
"""
import uuid

from httpx import AsyncClient


class TestListsEndpoints:
    async def test_get_lists(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/lists/",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200

    async def test_create_list(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/lists/",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )
        assert response.status_code == 201

    async def test_get_list_by_id(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/lists/{list_id}",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200

    async def test_update_list(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/lists/{list_id}",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )
        assert response.status_code == 200

    async def test_delete_list(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/lists/{list_id}",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 204


class TestListItemsEndpoints:
    async def test_get_items(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/lists/{list_id}/items",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200

    async def test_create_item(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/lists/{list_id}/items",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )
        assert response.status_code == 201

    async def test_update_item(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        item_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )
        assert response.status_code == 200

    async def test_delete_item(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        item_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/lists/{list_id}/items/{item_id}",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 204


class TestListMembersEndpoints:
    async def test_get_members(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/lists/{list_id}/members",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200

    async def test_remove_member(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        member_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/lists/{list_id}/members/{member_id}",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 204


class TestListInvitationsEndpoints:
    async def test_invite_to_list(self, client: AsyncClient) -> None:
        list_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/lists/{list_id}/invite",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )
        assert response.status_code == 201

    async def test_get_invitation(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/invitations/some-token-abc")
        assert response.status_code == 200

    async def test_accept_invitation(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/invitations/some-token-abc/accept",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
