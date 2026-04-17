import uuid

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("/")
async def get_lists(current_user: dict = Depends(get_current_user)) -> list:
    # TODO: implementar — retorna llistes de l'usuari autenticat
    pass  # type: ignore[return-value]


@router.post("/", status_code=201)
async def create_list(current_user: dict = Depends(get_current_user)) -> dict:
    # TODO: implementar — crea una nova llista
    pass  # type: ignore[return-value]


@router.get("/{list_id}")
async def get_list(list_id: uuid.UUID, current_user: dict = Depends(get_current_user)) -> dict:
    # TODO: implementar — retorna una llista per id
    pass  # type: ignore[return-value]


@router.patch("/{list_id}")
async def update_list(list_id: uuid.UUID, current_user: dict = Depends(get_current_user)) -> dict:
    # TODO: implementar — actualitza una llista
    pass  # type: ignore[return-value]


@router.delete("/{list_id}", status_code=204)
async def delete_list(list_id: uuid.UUID, current_user: dict = Depends(get_current_user)) -> None:
    # TODO: implementar — elimina una llista
    pass
