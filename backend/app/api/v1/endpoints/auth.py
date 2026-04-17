import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import AUTH_LIMIT, limiter
from app.core.security import get_current_user, get_supabase
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
@limiter.limit(AUTH_LIMIT)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Email ja registrat", "code": "EMAIL_EXISTS"},
        )

    supabase = get_supabase()
    try:
        response = await asyncio.to_thread(
            supabase.auth.sign_up,
            {"email": body.email, "password": body.password},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": str(exc), "code": "SUPABASE_ERROR"},
        )

    if response.user:
        user_id = uuid.UUID(str(response.user.id))
        user = User(
            id=user_id,
            email=body.email,
            display_name=body.email.split("@")[0],
        )
        db.add(user)
        await db.commit()

    return {
        "user_id": str(response.user.id) if response.user else None,
        "email": body.email,
        "message": "Verifica el teu correu per activar el compte",
    }


@router.post("/login")
@limiter.limit(AUTH_LIMIT)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    supabase = get_supabase()
    try:
        response = await asyncio.to_thread(
            supabase.auth.sign_in_with_password,
            {"email": body.email, "password": body.password},
        )
    except Exception as exc:
        error_msg = str(exc).lower()
        if "rate limit" in error_msg or "too many" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"detail": "Massa intents. Torna-ho a provar més tard.", "code": "RATE_LIMIT"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Credencials incorrectes", "code": "INVALID_CREDENTIALS"},
        )

    if not response.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Credencials incorrectes", "code": "INVALID_CREDENTIALS"},
        )

    user_id = uuid.UUID(str(response.user.id))
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user:
        db_user.last_seen_at = datetime.now(timezone.utc)
        await db.commit()

    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        expires_in=response.session.expires_in or 900,
    )


@router.post("/logout")
@limiter.limit(AUTH_LIMIT)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict:
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header[len("Bearer "):] if auth_header.startswith("Bearer ") else ""

    if access_token:
        supabase = get_supabase()
        try:
            await asyncio.to_thread(supabase.auth.admin.sign_out, access_token)
        except Exception:
            pass  # Token ja invàlid o caducat

    return {"message": "Sessió tancada"}


@router.post("/refresh")
@limiter.limit(AUTH_LIMIT)
async def refresh(
    request: Request,
    body: RefreshRequest,
) -> TokenResponse:
    supabase = get_supabase()
    try:
        response = await asyncio.to_thread(
            supabase.auth.refresh_session,
            body.refresh_token,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Refresh token invàlid o caducat", "code": "INVALID_REFRESH_TOKEN"},
        )

    if not response.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Refresh token invàlid o caducat", "code": "INVALID_REFRESH_TOKEN"},
        )

    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        expires_in=response.session.expires_in or 900,
    )


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)
