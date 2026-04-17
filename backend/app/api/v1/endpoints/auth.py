from fastapi import APIRouter, Request

from app.core.limiter import AUTH_LIMIT, limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
@limiter.limit(AUTH_LIMIT)
async def register(request: Request) -> dict:
    # TODO: implementar — registre d'usuari via Supabase + crear fila a users
    pass  # type: ignore[return-value]


@router.post("/login")
@limiter.limit(AUTH_LIMIT)
async def login(request: Request) -> dict:
    # TODO: implementar — login via Supabase, retorna access + refresh tokens
    pass  # type: ignore[return-value]


@router.post("/logout")
@limiter.limit(AUTH_LIMIT)
async def logout(request: Request) -> dict:
    # TODO: implementar — invalida el refresh token
    pass  # type: ignore[return-value]


@router.post("/refresh")
@limiter.limit(AUTH_LIMIT)
async def refresh(request: Request) -> dict:
    # TODO: implementar — bescanvia refresh token per nous tokens
    pass  # type: ignore[return-value]
