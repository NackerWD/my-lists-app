"""Integration tests per als endpoints d'autenticació. BD i Supabase estan mockat."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.security import get_current_user
from main import app


def _mock_supabase_session(access: str = "access-token", refresh: str = "refresh-token") -> MagicMock:
    session = MagicMock()
    session.access_token = access
    session.refresh_token = refresh
    session.expires_in = 900
    return session


def _mock_sign_up_response(email: str = "test@test.com") -> MagicMock:
    user = MagicMock()
    user.id = str(uuid.uuid4())
    user.email = email
    resp = MagicMock()
    resp.user = user
    resp.session = None
    return resp


def _mock_sign_in_response(email: str = "test@test.com") -> MagicMock:
    user = MagicMock()
    user.id = str(uuid.uuid4())
    user.email = email
    resp = MagicMock()
    resp.user = user
    resp.session = _mock_supabase_session()
    return resp


class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = _mock_sign_up_response("new@test.com")
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "new@test.com", "password": "password12345"},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@test.com"
        assert "Verifica" in data["message"]

    async def test_register_duplicate_email(self, client: AsyncClient, mock_db: MagicMock) -> None:
        # Configura el mock de BD perquè retorni un usuari existent
        mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock()

        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@test.com", "password": "password12345"},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "EMAIL_EXISTS"

    async def test_register_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "any@test.com", "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = _mock_sign_in_response("user@test.com")
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "user@test.com", "password": "password12345"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = Exception("Invalid login credentials")
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@test.com", "password": "wrongpassword1"},
            )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


class TestRefresh:
    async def test_refresh_valid_token(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = _mock_sign_in_response()
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-refresh-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = Exception("Invalid refresh token")
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid-token"},
            )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"


class TestMe:
    async def test_me_no_token(self, client: AsyncClient) -> None:
        # Elimina l'override de get_current_user per testar el cas "sense autenticació"
        app.dependency_overrides.pop(get_current_user, None)

        response = await client.get("/api/v1/auth/me")
        # HTTPBearer llança 403 quan no hi ha header Authorization
        assert response.status_code in [401, 403]

    async def test_me_with_valid_token(self, client: AsyncClient) -> None:
        # get_current_user és ja override a mock_user via fixture autouse
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
