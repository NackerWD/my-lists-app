"""Tests unitaris per a les funcions de seguretat.
Supabase i la BD es mocken completament — no calen connexions externes.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import get_current_user, verify_supabase_token


def _make_credentials(token: str = "valid-token") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _make_mock_db(existing_user: object = None) -> AsyncMock:
    """Crea un AsyncSession mockat que retorna `existing_user` quan es consulta."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing_user
    db.execute = AsyncMock(return_value=result_mock)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestVerifySupabaseToken:
    async def test_valid_token_returns_payload(self) -> None:
        mock_resp = MagicMock()
        mock_resp.user = MagicMock()
        mock_resp.user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_resp.user.email = "user@example.com"

        with patch("app.core.security.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            payload = await verify_supabase_token(_make_credentials("good-token"))

        assert payload["sub"] == "550e8400-e29b-41d4-a716-446655440000"
        assert payload["email"] == "user@example.com"

    async def test_no_user_raises_401(self) -> None:
        mock_resp = MagicMock()
        mock_resp.user = None

        with patch("app.core.security.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            with pytest.raises(HTTPException) as exc_info:
                await verify_supabase_token(_make_credentials("bad-token"))

        assert exc_info.value.status_code == 401

    async def test_supabase_exception_raises_401(self) -> None:
        with patch("app.core.security.asyncio.to_thread", new_callable=AsyncMock) as m:
            m.side_effect = Exception("Supabase network error")
            with pytest.raises(HTTPException) as exc_info:
                await verify_supabase_token(_make_credentials("bad-token"))

        assert exc_info.value.status_code == 401
        assert "caducat" in exc_info.value.detail.lower() or "invàlid" in exc_info.value.detail.lower()


class TestGetCurrentUser:
    async def test_creates_new_user_on_first_login(self) -> None:
        """Quan l'usuari no existeix a la BD local, el crea automàticament."""
        user_id = str(uuid.uuid4())
        email = f"new-{uuid.uuid4().hex[:6]}@example.com"
        payload = {"sub": user_id, "email": email}
        mock_db = _make_mock_db(existing_user=None)

        await get_current_user(payload=payload, db=mock_db)  # type: ignore[arg-type]

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        # El nou usuari s'hauria d'haver afegit com a instància de User
        added_user = mock_db.add.call_args[0][0]
        assert str(added_user.id) == user_id
        assert added_user.email == email
        assert added_user.display_name == email.split("@")[0]

    async def test_returns_existing_user(self) -> None:
        """Quan l'usuari ja existeix a la BD, el retorna sense crear-ne un de nou."""
        user_id = str(uuid.uuid4())
        email = f"existing-{uuid.uuid4().hex[:6]}@example.com"
        payload = {"sub": user_id, "email": email}

        existing = MagicMock()
        existing.id = uuid.UUID(user_id)
        existing.email = email
        mock_db = _make_mock_db(existing_user=existing)

        user = await get_current_user(payload=payload, db=mock_db)  # type: ignore[arg-type]

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        assert user is existing
