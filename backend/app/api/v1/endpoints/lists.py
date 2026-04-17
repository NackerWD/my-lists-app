import uuid

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("/")
async def get_lists(current_user=Depends(get_current_user)):
    # TODO: implementar — retorna llistes de l'usuari autenticat
    return []


@router.post("/", status_code=201)
async def create_list(current_user=Depends(get_current_user)):
    # TODO: implementar — crea una nova llista
    return {}


@router.get("/{list_id}")
async def get_list(list_id: uuid.UUID, current_user=Depends(get_current_user)):
    # TODO: implementar — retorna una llista per id
    return {}


@router.patch("/{list_id}")
async def update_list(list_id: uuid.UUID, current_user=Depends(get_current_user)):
    # TODO: implementar — actualitza una llista
    return {}


@router.delete("/{list_id}", status_code=204)
async def delete_list(list_id: uuid.UUID, current_user=Depends(get_current_user)):
    # TODO: implementar — elimina una llista
    return {"deleted": True}
