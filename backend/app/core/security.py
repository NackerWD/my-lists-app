from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer()


def verify_supabase_token(token: str) -> dict:
    """Validate a Supabase JWT and return the decoded payload."""
    # TODO: implementar — validació real contra SUPABASE_URL/auth/v1/user
    # Placeholder: retorna un payload mock per no bloquejar el servidor durant dev
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
        )
    return {"sub": "00000000-0000-0000-0000-000000000000", "email": "dev@example.com", "role": "owner"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: extracts and validates Bearer token."""
    return verify_supabase_token(credentials.credentials)


def require_role(role: str):
    """Dependency factory: raises 403 if the user doesn't have the required role."""

    async def _check_role(current_user: dict = Depends(get_current_user)) -> dict:
        # TODO: implementar — comparació real de rols
        if current_user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return current_user

    return _check_role
