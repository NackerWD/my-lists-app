"""Tests d'integració per /api/v1/device-tokens (BD real, engine.begin() per seed)."""
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
OTHER_USER_ID = uuid.UUID("650e8400-e29b-41d4-a716-446655440001")


async def test_register_device_token_201(client_owner: AsyncClient) -> None:
    tid = str(uuid.uuid4())
    r = await client_owner.post(
        "/api/v1/device-tokens/",
        json={"token": f"integ-{tid}", "platform": "web"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["token"] == f"integ-{tid}"
    assert data["platform"] == "web"
    assert data["user_id"] == str(MOCK_USER_ID)


async def test_register_device_token_upsert(client_owner: AsyncClient) -> None:
    tok = f"upsert-{uuid.uuid4()}"
    r1 = await client_owner.post(
        "/api/v1/device-tokens/",
        json={"token": tok, "platform": "ios"},
    )
    assert r1.status_code == 201
    r2 = await client_owner.post(
        "/api/v1/device-tokens/",
        json={"token": tok, "platform": "android"},
    )
    assert r2.status_code == 201
    assert r2.json()["platform"] == "android"


async def test_unregister_device_token_200(client_owner: AsyncClient, test_engine: AsyncEngine) -> None:
    tok = f"del-{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    async with test_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO device_tokens (id, user_id, token, platform, created_at)
                VALUES (:id, :uid, :token, 'web', :now)
            """),
            {"id": str(uuid.uuid4()), "uid": str(MOCK_USER_ID), "token": tok, "now": now},
        )

    r = await client_owner.delete(f"/api/v1/device-tokens/{tok}")
    assert r.status_code == 200
    assert r.json() == {"deleted": True}


async def test_unregister_not_found(client_owner: AsyncClient) -> None:
    r = await client_owner.delete("/api/v1/device-tokens/nonexistent-token-xyz")
    assert r.status_code == 404


async def test_unregister_wrong_user_404(client: AsyncClient, test_engine: AsyncEngine) -> None:
    """Token d'un altre usuari: el client mock és MOCK_USER — no pot esborrar token d'OTHER."""
    tok = f"other-{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    async with test_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO device_tokens (id, user_id, token, platform, created_at)
                VALUES (:id, :uid, :token, 'web', :now)
            """),
            {"id": str(uuid.uuid4()), "uid": str(OTHER_USER_ID), "token": tok, "now": now},
        )

    r = await client.delete(f"/api/v1/device-tokens/{tok}")
    assert r.status_code == 404
