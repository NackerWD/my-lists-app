from fastapi import APIRouter

from app.api.v1.endpoints import auth, device_tokens, list_invitations, list_items, list_members, lists, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(device_tokens.router)
api_router.include_router(users.router)
api_router.include_router(lists.router)
api_router.include_router(list_items.router)
api_router.include_router(list_members.router)
api_router.include_router(list_invitations.router)
