"""Tests unitaris per al WebSocket handler."""
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.ws.handler as ws_handler
from app.ws.handler import broadcast, _connections as connections, _socket_users as socket_users


class TestBroadcast:
    async def test_broadcast_sends_to_all_sockets(self) -> None:
        list_id = "test-list-broadcast"
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        connections[list_id] = {ws1, ws2}

        await broadcast(list_id, {"event": "test"})

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

        del connections[list_id]

    async def test_broadcast_removes_dead_sockets(self) -> None:
        list_id = "test-list-dead"
        ws_ok = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_text.side_effect = Exception("connection closed")
        connections[list_id] = {ws_ok, ws_dead}

        await broadcast(list_id, {"event": "update"})

        ws_ok.send_text.assert_called_once()
        assert ws_dead not in connections[list_id]

        del connections[list_id]

    async def test_broadcast_empty_list(self) -> None:
        await broadcast("non-existent-list", {"event": "test"})

    async def test_broadcast_serializes_message(self) -> None:
        list_id = "test-list-serial"
        ws = AsyncMock()
        connections[list_id] = {ws}

        await broadcast(list_id, {"key": "value", "num": 42})

        call_args = ws.send_text.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["key"] == "value"
        assert parsed["num"] == 42

        del connections[list_id]

    async def test_broadcast_excludes_matching_socket_user(self) -> None:
        list_id = "test-list-exclude"
        ws_a = AsyncMock()
        ws_b = AsyncMock()
        connections[list_id] = {ws_a, ws_b}
        socket_users[ws_a] = "user-a"
        socket_users[ws_b] = "user-b"

        await broadcast(list_id, {"event": "x"}, exclude_user_id="user-a")

        ws_a.send_text.assert_not_called()
        ws_b.send_text.assert_called_once()

        del connections[list_id]
        socket_users.pop(ws_a, None)
        socket_users.pop(ws_b, None)


class TestPrivateWsHelpers:
    async def test_get_user_id_from_token_empty(self) -> None:
        assert await ws_handler._get_user_id_from_token("") is None

    async def test_is_list_member_invalid_uuid(self) -> None:
        lid = str(uuid.uuid4())
        assert await ws_handler._is_list_member("not-a-uuid", lid) is False
        assert await ws_handler._is_list_member(lid, "not-a-uuid") is False

    async def test_is_list_member_with_mock_session(self) -> None:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = object()
        mock_session.execute = AsyncMock(return_value=mock_result)

        class FakeCM:
            def __init__(self, s: AsyncMock) -> None:
                self._s = s

            async def __aenter__(self) -> AsyncMock:
                return self._s

            async def __aexit__(self, *args: object) -> None:
                return None

        with patch.object(ws_handler, "AsyncSessionLocal", return_value=FakeCM(mock_session)):
            ok = await ws_handler._is_list_member(
                str(uuid.uuid4()),
                str(uuid.uuid4()),
            )
        assert ok is True

        mock_result.scalar_one_or_none.return_value = None
        with patch.object(ws_handler, "AsyncSessionLocal", return_value=FakeCM(mock_session)):
            missing = await ws_handler._is_list_member(
                str(uuid.uuid4()),
                str(uuid.uuid4()),
            )
        assert missing is False


class TestSafeBroadcast:
    @pytest.mark.asyncio
    async def test_safe_broadcast_delegates_to_broadcast(self) -> None:
        with patch.object(ws_handler, "broadcast", new_callable=AsyncMock) as mock_bc:
            await ws_handler._safe_broadcast("list-1", {"type": "x"}, exclude_user_id="u1")
        mock_bc.assert_awaited_once_with("list-1", {"type": "x"}, "u1")

    @pytest.mark.asyncio
    async def test_safe_broadcast_logs_when_broadcast_raises(self) -> None:
        with patch.object(ws_handler, "broadcast", new_callable=AsyncMock, side_effect=RuntimeError("boom")):
            with patch.object(ws_handler.logger, "warning") as mock_log:
                await ws_handler._safe_broadcast("list-1", {"type": "x"})
        mock_log.assert_called_once()


class TestHeartbeatLoop:
    @pytest.mark.asyncio
    async def test_heartbeat_sends_ping_after_sleep(self) -> None:
        ws = AsyncMock()
        real_sleep = asyncio.sleep

        async def sleep_shim(_delay: float) -> None:
            await real_sleep(0)

        with patch.object(ws_handler.asyncio, "sleep", side_effect=sleep_shim):
            task = asyncio.create_task(ws_handler._heartbeat_loop(ws, "lid", "uid"))
            await real_sleep(0.02)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        ws.send_text.assert_awaited()
        sent = json.loads(ws.send_text.await_args[0][0])
        assert sent["type"] == "ping"
