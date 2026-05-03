import asyncio
import functools
import logging
from datetime import datetime, timezone

import firebase_admin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from firebase_admin import messaging
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.device_token import DeviceToken
from app.models.list_item import ListItem

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_reminders() -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ListItem).where(
                ListItem.remind_at.is_not(None),
                ListItem.remind_at <= now,
                ListItem.is_checked.is_(False),
                ListItem.reminded_at.is_(None),
            )
        )
        items = result.scalars().all()
        for item in items:
            if item.created_by is not None:
                tokens_result = await db.execute(
                    select(DeviceToken).where(DeviceToken.user_id == item.created_by)
                )
                for token in tokens_result.scalars().all():
                    await _send_push(token.token, item)
            item.reminded_at = now
        await db.commit()


async def _send_push(token: str, item: ListItem) -> None:
    """Envia push notification via FCM (firebase-admin)."""
    if not firebase_admin._apps:
        logger.warning("Firebase Admin no inicialitzat — push notification omesa")
        return

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="MasterList",
                body=item.content,
            ),
            data={
                "list_id": str(item.list_id),
                "item_id": str(item.id),
            },
            token=token,
        )
        send_each_async = getattr(messaging, "send_each_async", None)
        if send_each_async is not None:
            response = await send_each_async([message])
            logger.info(
                "Push enviat: %s ok, %s errors",
                response.success_count,
                response.failure_count,
            )
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, functools.partial(messaging.send, message))
            logger.info("Push enviat (fallback sync messaging.send)")
    except Exception as e:
        prefix = token[:10] if len(token) >= 10 else token
        logger.error("Error enviant push a %s...: %s", prefix, e)


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(send_reminders, "interval", minutes=1, id="send_reminders")
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
