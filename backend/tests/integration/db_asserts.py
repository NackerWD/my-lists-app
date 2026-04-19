"""Asserts sobre la BD per a tests d'integració (mateixa visibilitat que ``db_session`` del client)."""
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def assert_list_exists(db: AsyncSession, list_id: uuid.UUID) -> None:
    res = await db.execute(
        text("SELECT 1 FROM lists WHERE id = CAST(:list_id AS uuid)"),
        {"list_id": str(list_id)},
    )
    row = res.scalar_one_or_none()
    assert row == 1, f"expected lists row for id={list_id}, visible to app db_session"


async def assert_list_member_exists(
    db: AsyncSession, list_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    res = await db.execute(
        text(
            "SELECT 1 FROM list_members WHERE list_id = CAST(:list_id AS uuid) "
            "AND user_id = CAST(:user_id AS uuid)"
        ),
        {"list_id": str(list_id), "user_id": str(user_id)},
    )
    row = res.scalar_one_or_none()
    assert row == 1, (
        f"expected list_members row list_id={list_id} user_id={user_id}, "
        "visible to app db_session"
    )


async def assert_list_and_membership(
    db: AsyncSession, list_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await assert_list_exists(db, list_id)
    await assert_list_member_exists(db, list_id, user_id)


async def assert_list_items_count(
    db: AsyncSession, list_id: uuid.UUID, expected: int
) -> None:
    res = await db.execute(
        text(
            "SELECT COUNT(*)::int FROM list_items "
            "WHERE list_id = CAST(:list_id AS uuid)"
        ),
        {"list_id": str(list_id)},
    )
    n = res.scalar_one()
    assert n == expected, (
        f"expected {expected} list_items for list_id={list_id}, got {n} in db_session"
    )


async def assert_list_members_count_at_least(
    db: AsyncSession, list_id: uuid.UUID, at_least: int
) -> None:
    res = await db.execute(
        text(
            "SELECT COUNT(*)::int FROM list_members "
            "WHERE list_id = CAST(:list_id AS uuid)"
        ),
        {"list_id": str(list_id)},
    )
    n = res.scalar_one()
    assert n >= at_least, (
        f"expected at least {at_least} list_members for list_id={list_id}, got {n}"
    )


async def assert_members_join_users_possible(
    db: AsyncSession, list_id: uuid.UUID, at_least: int
) -> None:
    """Comprova que el join ListMember/User del GET /members tindrà files."""
    res = await db.execute(
        text(
            "SELECT COUNT(*)::int FROM list_members lm "
            "INNER JOIN users u ON u.id = lm.user_id "
            "WHERE lm.list_id = CAST(:list_id AS uuid)"
        ),
        {"list_id": str(list_id)},
    )
    n = res.scalar_one()
    assert n >= at_least, (
        f"expected at least {at_least} member rows joinable to users for list_id={list_id}"
    )
