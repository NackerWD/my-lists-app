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
