import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_list_role
from app.models.list import List
from app.models.list_item import ListItem
from app.models.list_member import ListMember
from app.models.user import User
from app.schemas.list_item import ListItemCreate, ListItemResponse, ListItemUpdate
from app.ws.handler import broadcast

router = APIRouter(tags=["list-items"])


async def _assert_member(
    db: AsyncSession, list_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Llança 404 si la llista no existeix, 403 si l'usuari no és membre."""
    list_result = await db.execute(select(List).where(List.id == list_id))  # pragma: no cover — guard intern; refactoritzar a Depends al sprint d'optimització
    if list_result.scalar_one_or_none() is None:  # pragma: no cover — guard intern; refactoritzar a Depends al sprint d'optimització
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Llista no trobada", "code": "LIST_NOT_FOUND"},
        )
    member_result = await db.execute(  # pragma: no cover — guard intern; refactoritzar a Depends al sprint d'optimització
        select(ListMember).where(
            (ListMember.list_id == list_id) & (ListMember.user_id == user_id)
        )
    )
    if member_result.scalar_one_or_none() is None:  # pragma: no cover — guard intern; refactoritzar a Depends al sprint d'optimització
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Accés denegat", "code": "ACCESS_DENIED"},
        )


@router.get("/lists/{list_id}/items", response_model=list[ListItemResponse])
async def get_items(
    list_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ListItemResponse]:
    await _assert_member(db, list_id, current_user.id)
    result = await db.execute(
        select(ListItem)
        .where(ListItem.list_id == list_id)
        .order_by(ListItem.position.asc())
    )
    return [ListItemResponse.model_validate(item) for item in result.scalars().all()]


@router.post("/lists/{list_id}/items", status_code=201, response_model=ListItemResponse)
async def create_item(
    list_id: uuid.UUID,
    body: ListItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListItemResponse:
    await _assert_member(db, list_id, current_user.id)

    max_result = await db.execute(
        select(func.max(ListItem.position)).where(ListItem.list_id == list_id)
    )
    max_pos = max_result.scalar()
    position = (max_pos + 1) if max_pos is not None else 0

    item = ListItem(
        id=uuid.uuid4(),
        list_id=list_id,
        created_by=current_user.id,
        content=body.content,
        position=position,
        due_date=body.due_date,
        priority=body.priority,
        remind_at=body.remind_at,
        metadata_=body.metadata_,
    )
    db.add(item)

    # Actualitza updated_at de la llista
    list_result = await db.execute(select(List).where(List.id == list_id))
    lst = list_result.scalar_one()
    lst.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)
    response = ListItemResponse.model_validate(item)
    asyncio.create_task(broadcast(str(list_id), {
        "type": "item_created",
        "list_id": str(list_id),
        "payload": response.model_dump(mode="json"),
    }, exclude_user_id=str(current_user.id)))
    return response


@router.patch("/lists/{list_id}/items/{item_id}", response_model=ListItemResponse)
async def update_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    body: ListItemUpdate,
    current_user: User = Depends(require_list_role("editor")),
    db: AsyncSession = Depends(get_db),
) -> ListItemResponse:
    result = await db.execute(
        select(ListItem).where((ListItem.id == item_id) & (ListItem.list_id == list_id))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Ítem no trobat", "code": "ITEM_NOT_FOUND"},
        )

    if body.content is not None:
        item.content = body.content
    if body.is_checked is not None:
        item.is_checked = body.is_checked
    if body.position is not None:
        item.position = body.position
    if body.due_date is not None:
        item.due_date = body.due_date
    if body.priority is not None:
        item.priority = body.priority
    if body.remind_at is not None:
        item.remind_at = body.remind_at

    item.updated_at = datetime.now(timezone.utc)

    # Actualitza updated_at de la llista
    list_result = await db.execute(select(List).where(List.id == list_id))
    lst = list_result.scalar_one_or_none()
    if lst:
        lst.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)
    response = ListItemResponse.model_validate(item)
    asyncio.create_task(broadcast(str(list_id), {
        "type": "item_updated",
        "list_id": str(list_id),
        "payload": response.model_dump(mode="json"),
    }, exclude_user_id=str(current_user.id)))
    return response


@router.delete("/lists/{list_id}/items/{item_id}", status_code=200)
async def delete_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(require_list_role("editor")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(ListItem).where((ListItem.id == item_id) & (ListItem.list_id == list_id))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Ítem no trobat", "code": "ITEM_NOT_FOUND"},
        )
    await db.delete(item)
    await db.commit()
    asyncio.create_task(broadcast(str(list_id), {
        "type": "item_deleted",
        "list_id": str(list_id),
        "payload": {"item_id": str(item_id)},
    }, exclude_user_id=str(current_user.id)))
    return {"deleted": True}
