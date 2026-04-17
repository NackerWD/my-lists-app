import uuid

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(tags=["list-items"])


@router.get("/lists/{list_id}/items")
async def get_items(list_id: uuid.UUID, current_user: dict = Depends(get_current_user)) -> list:
    # TODO: implementar — retorna els ítems d'una llista
    pass  # type: ignore[return-value]


@router.post("/lists/{list_id}/items", status_code=201)
async def create_item(list_id: uuid.UUID, current_user: dict = Depends(get_current_user)) -> dict:
    # TODO: implementar — crea un ítem a la llista
    pass  # type: ignore[return-value]


@router.patch("/lists/{list_id}/items/{item_id}")
async def update_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
) -> dict:
    # TODO: implementar — actualitza un ítem
    pass  # type: ignore[return-value]


@router.delete("/lists/{list_id}/items/{item_id}", status_code=204)
async def delete_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
) -> None:
    # TODO: implementar — elimina un ítem
    pass
