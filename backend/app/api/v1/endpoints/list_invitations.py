import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user

router = APIRouter(tags=["list-invitations"])


@router.post("/lists/{list_id}/invite", status_code=201)
async def invite_to_list(
    list_id: uuid.UUID, current_user=Depends(get_current_user)
):
    # Stub — implementar al Sprint 4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"detail": "Not implemented — Sprint 4", "code": "NOT_IMPLEMENTED"},
    )


@router.get("/invitations/{token}")
async def get_invitation(token: str):
    # Stub — implementar al Sprint 4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"detail": "Not implemented — Sprint 4", "code": "NOT_IMPLEMENTED"},
    )


@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str, current_user=Depends(get_current_user)
):
    # Stub — implementar al Sprint 4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"detail": "Not implemented — Sprint 4", "code": "NOT_IMPLEMENTED"},
    )
