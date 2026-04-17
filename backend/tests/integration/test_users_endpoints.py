"""Integration tests per als endpoints /users/me."""
from httpx import AsyncClient


class TestUsersMe:
    async def test_get_me_returns_profile(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"

    async def test_patch_me_updates_display_name(self, client: AsyncClient) -> None:
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
            json={"display_name": "Nou Nom"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Nou Nom"

    async def test_patch_me_updates_avatar_url(self, client: AsyncClient) -> None:
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer valid-token"},
            json={"avatar_url": "https://example.com/avatar.png"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["avatar_url"] == "https://example.com/avatar.png"

    async def test_get_me_no_token(self, client: AsyncClient) -> None:
        from app.core.security import get_current_user
        from main import app

        app.dependency_overrides.pop(get_current_user, None)
        response = await client.get("/api/v1/users/me")
        assert response.status_code in [401, 403]
