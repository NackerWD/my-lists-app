import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.security import verify_supabase_token

ws_router = APIRouter()

# Active connections per list: { list_id: { websocket, ... } }
connections: dict[str, set[WebSocket]] = {}


async def broadcast(list_id: str, message: dict, exclude_user_id: str | None = None) -> None:
    """Send a JSON message to all connected clients of a list, optionally excluding one user."""
    sockets = connections.get(list_id, set())
    dead: set[WebSocket] = set()
    for ws in sockets:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead.add(ws)
    for ws in dead:
        sockets.discard(ws)


@ws_router.websocket("/ws/lists/{list_id}")
async def websocket_endpoint(websocket: WebSocket, list_id: str, token: str = "") -> None:
    try:
        payload = verify_supabase_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    user_id: str = payload.get("sub", "")

    connections.setdefault(list_id, set()).add(websocket)
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
        connections[list_id].discard(websocket)
