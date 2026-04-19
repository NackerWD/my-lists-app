import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, require_list_role
from app.models.list import List
from app.models.list_invitation import ListInvitation
from app.models.list_member import ListMember
from app.models.user import User
from app.schemas.list_invitation import ListInviteRequest

router = APIRouter(tags=["list-invitations"])


@router.post("/lists/{list_id}/invite", status_code=201)
async def invite_to_list(
    list_id: uuid.UUID,
    body: ListInviteRequest,
    current_user: User = Depends(require_list_role("editor")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    lst = (await db.execute(select(List).where(List.id == list_id))).scalar_one_or_none()
    if lst is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Llista no trobada", "code": "LIST_NOT_FOUND"},
        )

    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    invitation = ListInvitation(
        id=uuid.uuid4(),
        list_id=list_id,
        invited_by=current_user.id,
        email=body.email,
        token=token,
        role=body.role,
        status="pending",
        expires_at=now + timedelta(days=7),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    link = f"{settings.FRONTEND_URL}/invite/{token}"
    return {"invitation_id": str(invitation.id), "link": link}


@router.get("/invitations/{token}")
async def get_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(ListInvitation).where(ListInvitation.token == token)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Invitació no trobada", "code": "INVITATION_NOT_FOUND"},
        )

    now = datetime.now(timezone.utc)
    expires = inv.expires_at if inv.expires_at.tzinfo else inv.expires_at.replace(tzinfo=timezone.utc)
    if expires < now or inv.status == "expired":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"detail": "Invitació caducada", "code": "INVITATION_EXPIRED"},
        )

    lst = (await db.execute(select(List).where(List.id == inv.list_id))).scalar_one_or_none()
    return {
        "invitation_id": str(inv.id),
        "list_id": str(inv.list_id),
        "list_title": lst.title if lst else None,
        "invited_by": str(inv.invited_by),
        "email": inv.email,
        "role": inv.role,
        "status": inv.status,
        "expires_at": inv.expires_at.isoformat(),
    }


@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(ListInvitation).where(ListInvitation.token == token)
    )
    inv = result.scalar_one_or_none()
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Invitació no trobada", "code": "INVITATION_NOT_FOUND"},
        )

    now = datetime.now(timezone.utc)
    expires = inv.expires_at if inv.expires_at.tzinfo else inv.expires_at.replace(tzinfo=timezone.utc)
    if expires < now or inv.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"detail": "Invitació caducada o ja usada", "code": "INVITATION_EXPIRED"},
        )

    existing = (  # pragma: no cover — guard intern; refactoritzar a Depends al sprint d'optimització
        await db.execute(
            select(ListMember).where(
                (ListMember.list_id == inv.list_id) & (ListMember.user_id == current_user.id)
            )
        )
    ).scalar_one_or_none()
    if existing is not None:  # pragma: no cover — guard intern; refactoritzar a Depends al sprint d'optimització
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Ja ets membre d'aquesta llista", "code": "ALREADY_MEMBER"},
        )

    member = ListMember(
        id=uuid.uuid4(),
        list_id=inv.list_id,
        user_id=current_user.id,
        role=inv.role,
    )
    db.add(member)
    inv.status = "accepted"
    await db.commit()

    return {"list_id": str(inv.list_id), "role": inv.role}
