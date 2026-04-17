"""Tests unitaris per al WebSocket handler."""
from unittest.mock import AsyncMock


from app.ws.handler import broadcast, connections


class TestBroadcast:
    async def test_broadcast_sends_to_all_sockets(self) -> None:
        list_id = "test-list-broadcast"
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        connections[list_id] = {ws1, ws2}

        await broadcast(list_id, {"event": "test"})

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

        # Neteja
        del connections[list_id]

    async def test_broadcast_removes_dead_sockets(self) -> None:
        list_id = "test-list-dead"
        ws_ok = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_text.side_effect = Exception("connection closed")
        connections[list_id] = {ws_ok, ws_dead}

        await broadcast(list_id, {"event": "update"})

        ws_ok.send_text.assert_called_once()
        # El socket mort s'ha d'haver eliminat del conjunt
        assert ws_dead not in connections[list_id]

        del connections[list_id]

    async def test_broadcast_empty_list(self) -> None:
        # Llista sense connexions — no ha de llançar excepcions
        await broadcast("non-existent-list", {"event": "test"})

    async def test_broadcast_serializes_message(self) -> None:
        import json
        list_id = "test-list-serial"
        ws = AsyncMock()
        connections[list_id] = {ws}

        await broadcast(list_id, {"key": "value", "num": 42})

        call_args = ws.send_text.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["key"] == "value"
        assert parsed["num"] == 42

        del connections[list_id]
