import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
    logger.info("PUSH → %s: %s", token, item.content)


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(send_reminders, "interval", minutes=1, id="send_reminders")
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
