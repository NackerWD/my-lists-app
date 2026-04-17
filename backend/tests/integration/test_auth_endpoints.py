"""Integration tests per als endpoints d'autenticació. Supabase és mockat."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _mock_supabase_user(email: str = "test@test.com") -> MagicMock:
    user = MagicMock()
    user.id = str(uuid.uuid4())
    user.email = email
    return user


def _mock_supabase_session(access: str = "access-token", refresh: str = "refresh-token") -> MagicMock:
    session = MagicMock()
    session.access_token = access
    session.refresh_token = refresh
    session.expires_in = 900
    return session


def _mock_sign_up_response(email: str = "test@test.com") -> MagicMock:
    resp = MagicMock()
    resp.user = _mock_supabase_user(email)
    resp.session = None
    return resp


def _mock_sign_in_response(email: str = "test@test.com") -> MagicMock:
    resp = MagicMock()
    resp.user = _mock_supabase_user(email)
    resp.session = _mock_supabase_session()
    return resp


class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = _mock_sign_up_response()
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "new@test.com", "password": "password12345"},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@test.com"
        assert "Verifica" in data["message"]

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        email = f"dup-{uuid.uuid4().hex[:6]}@test.com"
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = _mock_sign_up_response(email)
            await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "password12345"},
            )
            # Second attempt — local DB should detect duplicate
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "password12345"},
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
        # Registra l'usuari primer
        email = f"login-{uuid.uuid4().hex[:6]}@test.com"
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = _mock_sign_up_response(email)
            await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "password12345"},
            )

        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = _mock_sign_in_response(email)
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "password12345"},
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
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    async def test_me_with_valid_token(self, client: AsyncClient) -> None:
        email = f"me-{uuid.uuid4().hex[:6]}@test.com"
        user_id = str(uuid.uuid4())

        mock_user_resp = MagicMock()
        mock_user_resp.user = MagicMock()
        mock_user_resp.user.id = user_id
        mock_user_resp.user.email = email

        with patch("app.core.security.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = mock_user_resp
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
