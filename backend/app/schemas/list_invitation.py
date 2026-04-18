import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


class ListInvitationBase(BaseModel):
    email: EmailStr


class ListInviteRequest(BaseModel):
    email: EmailStr
    role: Literal["editor", "viewer"] = "viewer"


class ListInvitationCreate(ListInvitationBase):
    role: Literal["editor", "viewer"] = "viewer"


class ListInvitationUpdate(BaseModel):
    status: Literal["pending", "accepted", "expired"]


class ListInvitationResponse(ListInvitationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_id: uuid.UUID
    invited_by: uuid.UUID
    token: str
    role: Literal["editor", "viewer"]
    status: Literal["pending", "accepted", "expired"]
    expires_at: datetime
    created_at: datetime
