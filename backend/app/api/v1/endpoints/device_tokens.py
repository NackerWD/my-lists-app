import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.device_token import DeviceToken
from app.models.user import User
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenResponse

router = APIRouter(prefix="/device-tokens", tags=["device-tokens"])


@router.post("/", status_code=201, response_model=DeviceTokenResponse)
async def register_device_token(
    body: DeviceTokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceTokenResponse:
    result = await db.execute(select(DeviceToken).where(DeviceToken.token == body.token))
    row = result.scalar_one_or_none()
    if row is not None:
        row.user_id = current_user.id
        row.platform = body.platform
        await db.commit()
        await db.refresh(row)
        return DeviceTokenResponse.model_validate(row)

    dt = DeviceToken(
        id=uuid.uuid4(),
        user_id=current_user.id,
        token=body.token,
        platform=body.platform,
    )
    db.add(dt)
    await db.commit()
    await db.refresh(dt)
    return DeviceTokenResponse.model_validate(dt)


@router.delete("/{token}", status_code=200)
async def unregister_device_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(DeviceToken).where(
            DeviceToken.token == token,
            DeviceToken.user_id == current_user.id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Token no trobat", "code": "DEVICE_TOKEN_NOT_FOUND"},
        )
    await db.delete(row)
    await db.commit()
    return {"deleted": True}
