"""Tests unitaris dels endpoints ``device_tokens`` (AsyncSession mockat)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient

from app.models.device_token import DeviceToken
from tests.unit.conftest import MOCK_USER_ID


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _exec_scalar_one_or_none(value):
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    return r


class TestRegisterDeviceTokenUnit:
    async def test_register_device_token(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(None))

        r = await client.post(
            "/api/v1/device-tokens/",
            json={"token": "fcm-token-abc", "platform": "android"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["token"] == "fcm-token-abc"
        assert data["platform"] == "android"
        assert data["user_id"] == str(MOCK_USER_ID)
        assert "id" in data
        assert "created_at" in data
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()

    async def test_register_device_token_upsert(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        existing = DeviceToken(
            id=uuid.uuid4(),
            user_id=MOCK_USER_ID,
            token="same-token",
            platform="ios",
            created_at=_now(),
        )
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(existing))

        r = await client.post(
            "/api/v1/device-tokens/",
            json={"token": "same-token", "platform": "web"},
        )
        assert r.status_code == 201
        assert r.json()["platform"] == "web"
        mock_db.add.assert_not_called()
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()


class TestUnregisterDeviceTokenUnit:
    async def test_unregister_device_token(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        row = DeviceToken(
            id=uuid.uuid4(),
            user_id=MOCK_USER_ID,
            token="tok-del",
            platform="android",
            created_at=_now(),
        )
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(row))

        r = await client.delete("/api/v1/device-tokens/tok-del")
        assert r.status_code == 200
        assert r.json() == {"deleted": True}
        mock_db.delete.assert_awaited_once()
        mock_db.commit.assert_awaited()

    async def test_unregister_not_found(
        self, client_full_bypass: tuple[AsyncClient, AsyncMock]
    ) -> None:
        client, mock_db = client_full_bypass
        mock_db.execute = AsyncMock(return_value=_exec_scalar_one_or_none(None))

        r = await client.delete("/api/v1/device-tokens/missing")
        assert r.status_code == 404
        body = r.json()
        assert "detail" in body
        inner = body["detail"] if isinstance(body["detail"], dict) else body
        assert inner.get("code") == "DEVICE_TOKEN_NOT_FOUND"
