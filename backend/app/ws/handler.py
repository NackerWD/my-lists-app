import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_supabase
from app.models.list_member import ListMember

ws_router = APIRouter()

# Active connections per list: { list_id: { websocket, ... } }
_connections: dict[str, set[WebSocket]] = {}
# Per-socket user mapping to support exclusion in broadcast
_socket_users: dict[WebSocket, str] = {}


async def broadcast(list_id: str, message: dict, exclude_user_id: str | None = None) -> None:
    """Send a JSON message to all connected clients of a list, optionally excluding one user."""
    dead: set[WebSocket] = set()
    for ws in _connections.get(list_id, set()).copy():
        if exclude_user_id and _socket_users.get(ws) == exclude_user_id:
            continue
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections[list_id].discard(ws)
        _socket_users.pop(ws, None)


async def _get_user_id_from_token(token: str) -> str | None:
    """Validate a raw Supabase JWT and return the user's UUID string, or None if invalid."""
    if not token:
        return None
    try:
        supabase = get_supabase()
        response = await asyncio.to_thread(supabase.auth.get_user, token)
        if response.user:
            return str(response.user.id)
    except Exception:
        pass
    return None


async def _is_list_member(list_id_str: str, user_id_str: str) -> bool:
    """Return True if the user is a member of the given list."""
    try:
        list_uuid = uuid.UUID(list_id_str)
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        return False
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ListMember).where(
                (ListMember.list_id == list_uuid) & (ListMember.user_id == user_uuid)
            )
        )
        return result.scalar_one_or_none() is not None


@ws_router.websocket("/ws/lists/{list_id}")
async def websocket_endpoint(websocket: WebSocket, list_id: str, token: str = "") -> None:  # pragma: no cover
    user_id = await _get_user_id_from_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not await _is_list_member(list_id, user_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    _connections.setdefault(list_id, set()).add(websocket)
    _socket_users[websocket] = user_id

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message: dict = json.loads(raw)
            except json.JSONDecodeError:
                continue

            message["user_id"] = user_id
            await broadcast(list_id, message, exclude_user_id=user_id)
    except WebSocketDisconnect:
        _connections[list_id].discard(websocket)
        _socket_users.pop(websocket, None)
        if not _connections.get(list_id):
            _connections.pop(list_id, None)
