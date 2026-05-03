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
from app.models.list_type import ListType
from app.models.user import User
from app.schemas.list import ListCreate, ListResponse, ListUpdate
from app.ws.handler import _safe_broadcast

router = APIRouter(prefix="/lists", tags=["lists"])


def _select_list_with_type(list_id: uuid.UUID):
    return (
        select(List, ListType.slug, ListType.label)
        .outerjoin(ListType, List.list_type_id == ListType.id)
        .where(List.id == list_id)
    )


async def _fetch_list_bundle(db: AsyncSession, list_id: uuid.UUID) -> tuple[List, str | None, str | None] | None:
    row = (await db.execute(_select_list_with_type(list_id))).one_or_none()
    if row is None:
        return None
    lst, slug, label = row
    return lst, slug, label


async def _to_response(
    db: AsyncSession,
    lst: List,
    *,
    list_type_slug: str | None = None,
    list_type_label: str | None = None,
) -> ListResponse:
    mc_sq = (
        select(func.count(ListMember.id))
        .where(ListMember.list_id == lst.id)
        .scalar_subquery()
    )
    ic_sq = (
        select(func.count(ListItem.id))
        .where(ListItem.list_id == lst.id)
        .scalar_subquery()
    )
    row = (await db.execute(select(mc_sq, ic_sq))).one()
    data = ListResponse.model_validate(lst)
    data.member_count = int(row[0])
    data.item_count = int(row[1])
    data.list_type_slug = list_type_slug
    data.list_type_label = list_type_label
    return data


@router.get("/", response_model=list[ListResponse])
async def get_lists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ListResponse]:
    member_count_sq = (
        select(func.count(ListMember.id))
        .where(ListMember.list_id == List.id)
        .correlate(List)
        .scalar_subquery()
    )
    item_count_sq = (
        select(func.count(ListItem.id))
        .where(ListItem.list_id == List.id)
        .correlate(List)
        .scalar_subquery()
    )
    stmt = (
        select(List, ListType.slug, ListType.label, member_count_sq, item_count_sq)
        .outerjoin(ListType, List.list_type_id == ListType.id)
        .join(ListMember, (ListMember.list_id == List.id) & (ListMember.user_id == current_user.id))
        .where(List.is_archived.is_(False))
        .order_by(List.updated_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    out: list[ListResponse] = []
    for lst, slug, label, mcnt, icnt in rows:
        data = ListResponse.model_validate(lst)
        data.member_count = int(mcnt)
        data.item_count = int(icnt)
        data.list_type_slug = slug
        data.list_type_label = label
        out.append(data)
    return out


@router.post("/", status_code=201, response_model=ListResponse)
async def create_list(
    body: ListCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListResponse:
    lst = List(
        id=uuid.uuid4(),
        owner_id=current_user.id,
        title=body.title,
        description=body.description,
        list_type_id=body.list_type_id,
    )
    db.add(lst)

    member = ListMember(
        id=uuid.uuid4(),
        list_id=lst.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)

    await db.commit()
    await db.refresh(lst)

    slug: str | None = None
    label: str | None = None
    if lst.list_type_id is not None:
        lt_row = await db.execute(select(ListType).where(ListType.id == lst.list_type_id))
        lt = lt_row.scalar_one_or_none()
        if lt is not None:
            slug, label = lt.slug, lt.label

    data = ListResponse.model_validate(lst)
    data.member_count = 1
    data.item_count = 0
    data.list_type_slug = slug
    data.list_type_label = label
    return data


@router.get("/{list_id}", response_model=ListResponse)
async def get_list(
    list_id: uuid.UUID,
    current_user: User = Depends(require_list_role("viewer")),
    db: AsyncSession = Depends(get_db),
) -> ListResponse:
    bundle = await _fetch_list_bundle(db, list_id)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Llista no trobada", "code": "LIST_NOT_FOUND"},
        )
    lst, slug, label = bundle
    return await _to_response(db, lst, list_type_slug=slug, list_type_label=label)


@router.patch("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: uuid.UUID,
    body: ListUpdate,
    current_user: User = Depends(require_list_role("editor")),
    db: AsyncSession = Depends(get_db),
) -> ListResponse:
    bundle = await _fetch_list_bundle(db, list_id)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Llista no trobada", "code": "LIST_NOT_FOUND"},
        )
    lst, _, _ = bundle

    if body.title is not None:
        lst.title = body.title
    if body.description is not None:
        lst.description = body.description
    if body.is_archived is not None:
        lst.is_archived = body.is_archived

    lst.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(lst)

    bundle2 = await _fetch_list_bundle(db, list_id)
    if bundle2 is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Llista no trobada", "code": "LIST_NOT_FOUND"},
        )
    lst2, slug2, label2 = bundle2

    response = await _to_response(db, lst2, list_type_slug=slug2, list_type_label=label2)
    asyncio.create_task(
        _safe_broadcast(
            str(list_id),
            {
                "type": "list_updated",
                "list_id": str(list_id),
                "payload": response.model_dump(mode="json"),
            },
            exclude_user_id=str(current_user.id),
        )
    )
    return response


@router.delete("/{list_id}", status_code=200)
async def delete_list(
    list_id: uuid.UUID,
    current_user: User = Depends(require_list_role("owner")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    bundle = await _fetch_list_bundle(db, list_id)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Llista no trobada", "code": "LIST_NOT_FOUND"},
        )
    lst, _, _ = bundle
    await db.delete(lst)
    await db.commit()
    asyncio.create_task(
        _safe_broadcast(
            str(list_id),
            {
                "type": "list_deleted",
                "list_id": str(list_id),
                "payload": {"list_id": str(list_id)},
            },
            exclude_user_id=str(current_user.id),
        )
    )
    return {"deleted": True}
