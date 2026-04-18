import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user

router = APIRouter(tags=["list-members"])


@router.get("/lists/{list_id}/members")
async def get_members(list_id: uuid.UUID, current_user=Depends(get_current_user)):
    # Stub — implementar al Sprint 4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"detail": "Not implemented — Sprint 4", "code": "NOT_IMPLEMENTED"},
    )


@router.delete("/lists/{list_id}/members/{member_id}", status_code=204)
async def remove_member(
    list_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user=Depends(get_current_user),
):
    # Stub — implementar al Sprint 4
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"detail": "Not implemented — Sprint 4", "code": "NOT_IMPLEMENTED"},
    )
