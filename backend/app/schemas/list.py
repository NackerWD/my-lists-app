import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListCreate(BaseModel):
    title: str
    description: str | None = None
    list_type_id: uuid.UUID | None = None


class ListUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_archived: bool | None = None


class ListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    list_type_id: uuid.UUID | None
    title: str
    description: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime | None
    member_count: int = 0
    item_count: int = 0
