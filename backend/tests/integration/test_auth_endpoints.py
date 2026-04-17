"""Integration tests per als endpoints d'autenticació amb PostgreSQL real.
Supabase (asyncio.to_thread) és mockat; la BD és real.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.core.security import get_current_user
from main import app


def _mock_sign_up_response(user_id: str | None = None, email: str = "test@test.com") -> MagicMock:
    user = MagicMock()
    user.id = user_id or str(uuid.uuid4())
    user.email = email
    resp = MagicMock()
    resp.user = user
    resp.session = None
    return resp


def _mock_sign_in_response(user_id: str | None = None, email: str = "test@test.com") -> MagicMock:
    user = MagicMock()
    user.id = user_id or str(uuid.uuid4())
    user.email = email
    session = MagicMock()
    session.access_token = "access-token"
    session.refresh_token = "refresh-token"
    session.expires_in = 900
    resp = MagicMock()
    resp.user = user
    resp.session = session
    return resp


class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.return_value = _mock_sign_up_response(email="unique1@test.com")
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "unique1@test.com", "password": "password12345"},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "unique1@test.com"
        assert "Verifica" in data["message"]

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        """Registra el mateix email dues vegades; la BD real detecta el duplicat."""
        email = f"dup-{uuid.uuid4().hex[:8]}@test.com"
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.return_value = _mock_sign_up_response(email=email)
            # Primer registre — ha de funcionar
            r1 = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "password12345"},
            )
            assert r1.status_code == 201

            # Segon registre — la BD local detecta el duplicat
            r2 = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "password12345"},
            )
        assert r2.status_code == 400
        assert r2.json()["detail"]["code"] == "EMAIL_EXISTS"

    async def test_register_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "any@test.com", "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.return_value = _mock_sign_in_response(email="loginuser@test.com")
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "loginuser@test.com", "password": "password12345"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.side_effect = Exception("Invalid login credentials")
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@test.com", "password": "wrongpassword1"},
            )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


class TestRefresh:
    async def test_refresh_valid_token(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.return_value = _mock_sign_in_response()
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-refresh-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        with patch("app.api.v1.endpoints.auth.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.side_effect = Exception("Invalid refresh token")
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid-token"},
            )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_REFRESH_TOKEN"


class TestMe:
    async def test_me_no_token(self, client: AsyncClient) -> None:
        # Elimina l'override de get_current_user per testar sense autenticació
        app.dependency_overrides.pop(get_current_user, None)
        response = await client.get("/api/v1/auth/me")
        # HTTPBearer retorna 403 quan no hi ha header Authorization
        assert response.status_code in [401, 403]

    async def test_me_with_valid_token(self, client: AsyncClient) -> None:
        # get_current_user ja és override a mock_current_user via fixture
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
