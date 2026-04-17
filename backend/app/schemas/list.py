import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListBase(BaseModel):
    title: str
    description: str | None = None
    list_type_id: uuid.UUID | None = None
    is_archived: bool = False


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    list_type_id: uuid.UUID | None = None
    is_archived: bool | None = None


class ListResponse(ListBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
