import uuid

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(tags=["list-members"])


@router.get("/lists/{list_id}/members")
async def get_members(list_id: uuid.UUID, current_user: dict = Depends(get_current_user)) -> list:
    # TODO: implementar — retorna els membres d'una llista
    pass  # type: ignore[return-value]


@router.delete("/lists/{list_id}/members/{member_id}", status_code=204)
async def remove_member(
    list_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
) -> None:
    # TODO: implementar — elimina un membre de la llista
    pass
