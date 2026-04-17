import uuid

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(tags=["list-invitations"])


@router.post("/lists/{list_id}/invite", status_code=201)
async def invite_to_list(
    list_id: uuid.UUID, current_user: dict = Depends(get_current_user)
) -> dict:
    # TODO: implementar — envia una invitació per email
    pass  # type: ignore[return-value]


@router.get("/invitations/{token}")
async def get_invitation(token: str) -> dict:
    # TODO: implementar — retorna detalls d'una invitació per token
    pass  # type: ignore[return-value]


@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str, current_user: dict = Depends(get_current_user)
) -> dict:
    # TODO: implementar — accepta una invitació i afegeix l'usuari a la llista
    pass  # type: ignore[return-value]
