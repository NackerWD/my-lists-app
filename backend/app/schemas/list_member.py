import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ListMemberBase(BaseModel):
    role: Literal["owner", "editor", "viewer"] = "viewer"


class ListMemberCreate(ListMemberBase):
    user_id: uuid.UUID


class ListMemberUpdate(BaseModel):
    role: Literal["owner", "editor", "viewer"]


class ListMemberResponse(ListMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime
