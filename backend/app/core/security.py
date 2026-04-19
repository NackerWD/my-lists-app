import asyncio
import uuid
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client, create_client

from app.core.config import settings
from app.core.database import get_db
from app.models.list_member import ListMember
from app.models.user import User

bearer_scheme = HTTPBearer()

ROLE_HIERARCHY: dict[str, int] = {"viewer": 0, "editor": 1, "owner": 2}

_supabase_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _supabase_client


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    supabase = get_supabase()
    try:
        response = await asyncio.to_thread(supabase.auth.get_user, credentials.credentials)
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invàlid",
            )
        return {
            "sub": str(response.user.id),
            "email": response.user.email,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invàlid o caducat",
        )


async def get_current_user(
    payload: dict = Depends(verify_supabase_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = uuid.UUID(payload["sub"])

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        # Primer login: crea el registre local sincronitzat amb el UUID de Supabase
        user = User(
            id=user_id,
            email=payload["email"],
            display_name=payload["email"].split("@")[0],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


@lru_cache(maxsize=None)
def require_list_role(minimum_role: str):
    """Factory de dependency que comprova el rol mínim de l'usuari a una llista.

    Retorna sempre la mateixa funció per a cada ``minimum_role`` (cache LRU),
    de manera que ``app.dependency_overrides[require_list_role("editor")]`` coincideix
    amb la instància usada a ``Depends(require_list_role("editor"))`` als routers.
    """

    async def _check(
        list_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        result = await db.execute(
            select(ListMember).where(
                ListMember.list_id == list_id,
                ListMember.user_id == current_user.id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"detail": "Accés denegat", "code": "ACCESS_DENIED"},
            )
        if ROLE_HIERARCHY.get(member.role, -1) < ROLE_HIERARCHY.get(minimum_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"detail": "Permisos insuficients", "code": "INSUFFICIENT_ROLE"},
            )
        return current_user

    return _check
