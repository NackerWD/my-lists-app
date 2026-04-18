"""Smoke test per a l'endpoint /health.
Verifica que el servei respon correctament — útil com a health check al CI i staging.
"""
from httpx import AsyncClient


class TestHealth:
    async def test_health_check(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
