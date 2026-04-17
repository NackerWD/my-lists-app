import uuid

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(tags=["list-items"])


@router.get("/lists/{list_id}/items")
async def get_items(list_id: uuid.UUID, current_user=Depends(get_current_user)):
    # TODO: implementar — retorna els ítems d'una llista
    return []


@router.post("/lists/{list_id}/items", status_code=201)
async def create_item(list_id: uuid.UUID, current_user=Depends(get_current_user)):
    # TODO: implementar — crea un ítem a la llista
    return {}


@router.patch("/lists/{list_id}/items/{item_id}")
async def update_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user=Depends(get_current_user),
):
    # TODO: implementar — actualitza un ítem
    return {}


@router.delete("/lists/{list_id}/items/{item_id}", status_code=204)
async def delete_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user=Depends(get_current_user),
):
    # TODO: implementar — elimina un ítem
    return {"deleted": True}
