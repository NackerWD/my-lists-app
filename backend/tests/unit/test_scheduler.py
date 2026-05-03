"""Tests unitaris del job de recordatoris (AsyncSessionLocal i _send_push mockats)."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.device_token import DeviceToken
from app.models.list_item import ListItem


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _exec_scalars_all(items: list):
    r = MagicMock()
    inner = MagicMock()
    inner.all.return_value = items
    r.scalars.return_value = inner
    return r


@pytest.mark.asyncio
async def test_no_items_to_remind() -> None:
    from app.scheduler import send_reminders

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_exec_scalars_all([]))
    db.commit = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=db)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.scheduler.AsyncSessionLocal", return_value=cm):
        with patch("app.scheduler._send_push", new_callable=AsyncMock) as mock_push:
            await send_reminders()
            mock_push.assert_not_awaited()


@pytest.mark.asyncio
async def test_sends_push_for_due_item() -> None:
    from app.scheduler import send_reminders

    past = _now() - timedelta(hours=1)
    uid = uuid.uuid4()
    item = ListItem(
        id=uuid.uuid4(),
        list_id=uuid.uuid4(),
        created_by=uid,
        content="Recorda'm",
        is_checked=False,
        position=0,
        remind_at=past,
        reminded_at=None,
        metadata_=None,
        priority=None,
        due_date=None,
    )
    token_row = DeviceToken(
        id=uuid.uuid4(),
        user_id=uid,
        token="push-tok",
        platform="android",
        created_at=_now(),
    )

    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _exec_scalars_all([item]),
            _exec_scalars_all([token_row]),
        ]
    )
    db.commit = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=db)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.scheduler.AsyncSessionLocal", return_value=cm):
        with patch("app.scheduler._send_push", new_callable=AsyncMock) as mock_push:
            await send_reminders()
            mock_push.assert_awaited_once()
            assert mock_push.await_args[0][0] == "push-tok"
            assert mock_push.await_args[0][1] is item


@pytest.mark.asyncio
async def test_skips_already_reminded() -> None:
    """La query exclou reminded_at; llista buida equival a cap ítem elegible."""
    from app.scheduler import send_reminders

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_exec_scalars_all([]))
    db.commit = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=db)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.scheduler.AsyncSessionLocal", return_value=cm):
        with patch("app.scheduler._send_push", new_callable=AsyncMock) as mock_push:
            await send_reminders()
            mock_push.assert_not_awaited()


@pytest.mark.asyncio
async def test_marks_reminded_at() -> None:
    from app.scheduler import send_reminders

    past = _now() - timedelta(minutes=5)
    item = ListItem(
        id=uuid.uuid4(),
        list_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        content="X",
        is_checked=False,
        position=0,
        remind_at=past,
        reminded_at=None,
        metadata_=None,
        priority=None,
        due_date=None,
    )

    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _exec_scalars_all([item]),
            _exec_scalars_all([]),
        ]
    )
    db.commit = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=db)
    cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.scheduler.AsyncSessionLocal", return_value=cm):
        with patch("app.scheduler._send_push", new_callable=AsyncMock):
            await send_reminders()
            assert item.reminded_at is not None
            db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_send_push_calls_fcm(mocker):
    """_send_push crida firebase_admin.messaging.send_each_async quan existeix."""
    mocker.patch("app.scheduler.firebase_admin._apps", {"default": object()})
    mock_send = mocker.patch(
        "app.scheduler.messaging.send_each_async",
        return_value=MagicMock(success_count=1, failure_count=0),
    )
    mock_item = MagicMock()
    mock_item.content = "Test ítem"
    mock_item.list_id = uuid.uuid4()
    mock_item.id = uuid.uuid4()

    from app.scheduler import _send_push

    await _send_push("fake-token-123", mock_item)

    mock_send.assert_called_once()
    call_args = mock_send.call_args[0][0]
    assert len(call_args) == 1
    assert call_args[0].token == "fake-token-123"


@pytest.mark.asyncio
async def test_send_push_without_firebase_init(mocker):
    """Sense Firebase inicialitzat no es crida FCM i no es propaga cap error."""
    mocker.patch("app.scheduler.firebase_admin._apps", {})
    mock_send = mocker.patch(
        "app.scheduler.messaging.send_each_async",
        side_effect=Exception("Firebase not initialized"),
    )
    mock_item = MagicMock()
    mock_item.content = "Test"
    mock_item.list_id = uuid.uuid4()
    mock_item.id = uuid.uuid4()

    from app.scheduler import _send_push

    await _send_push("fake-token", mock_item)

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_send_push_handles_invalid_token(mocker):
    """FCM pot reportar fallades per token; es registra i no es trenca el flux."""
    mocker.patch("app.scheduler.firebase_admin._apps", {"default": object()})
    mock_send = mocker.patch(
        "app.scheduler.messaging.send_each_async",
        return_value=MagicMock(success_count=0, failure_count=1),
    )
    mock_item = MagicMock()
    mock_item.content = "X"
    mock_item.list_id = uuid.uuid4()
    mock_item.id = uuid.uuid4()

    from app.scheduler import _send_push

    await _send_push("bad-token", mock_item)

    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_push_swallows_send_exception(mocker):
    """Si send_each_async falla, es captura i no es propaga."""
    mocker.patch("app.scheduler.firebase_admin._apps", {"default": object()})
    mocker.patch(
        "app.scheduler.messaging.send_each_async",
        side_effect=RuntimeError("network"),
    )
    mock_item = MagicMock()
    mock_item.content = "Test"
    mock_item.list_id = uuid.uuid4()
    mock_item.id = uuid.uuid4()

    from app.scheduler import _send_push

    await _send_push("fake-token", mock_item)
