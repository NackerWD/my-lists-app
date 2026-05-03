from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.list_type import ListType
from app.models.user import User
from app.schemas.list_type import ListTypeResponse

router = APIRouter(tags=["list-types"])  # prefix només a api/v1/router.py (include_router)


@router.get("/", response_model=list[ListTypeResponse])
async def get_list_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ListTypeResponse]:
    """Retorna tots els tipus de llista actius."""
    result = await db.execute(
        select(ListType).where(ListType.is_active.is_(True)).order_by(ListType.slug)
    )
    return list(result.scalars().all())
