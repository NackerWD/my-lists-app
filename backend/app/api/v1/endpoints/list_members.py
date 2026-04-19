import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_list_role
from app.models.list_member import ListMember
from app.models.user import User
from app.schemas.list_member import ListMemberWithUserResponse

router = APIRouter(tags=["list-members"])


@router.get("/lists/{list_id}/members", response_model=list[ListMemberWithUserResponse])
async def get_members(
    list_id: uuid.UUID,
    current_user: User = Depends(require_list_role("viewer")),
    db: AsyncSession = Depends(get_db),
) -> list[ListMemberWithUserResponse]:
    rows = (
        await db.execute(
            select(ListMember, User)
            .join(User, ListMember.user_id == User.id)
            .where(ListMember.list_id == list_id)
            .order_by(ListMember.joined_at.asc())
        )
    ).all()

    return [
        ListMemberWithUserResponse(
            id=member.id,
            list_id=member.list_id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            email=user.email,
            display_name=user.display_name,
        )
        for member, user in rows
    ]


@router.delete("/lists/{list_id}/members/{user_id}", status_code=200)
async def remove_member(
    list_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(require_list_role("owner")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    target = (
        await db.execute(
            select(ListMember).where(
                (ListMember.list_id == list_id) & (ListMember.user_id == user_id)
            )
        )
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Membre no trobat", "code": "MEMBER_NOT_FOUND"},
        )
    if target.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "No es pot eliminar l'owner", "code": "CANNOT_REMOVE_OWNER"},
        )

    await db.delete(target)
    await db.commit()
    return {"deleted": True}
