import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ListItemCreate(BaseModel):
    content: str
    due_date: datetime | None = None
    priority: Literal["high", "medium", "low"] | None = None
    remind_at: datetime | None = None
    metadata_: dict | None = None
    position: int = 0


class ListItemUpdate(BaseModel):
    content: str | None = None
    is_checked: bool | None = None
    position: int | None = None
    due_date: datetime | None = None
    priority: Literal["high", "medium", "low"] | None = None
    remind_at: datetime | None = None


class ListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_id: uuid.UUID
    created_by: uuid.UUID | None
    content: str
    is_checked: bool
    position: int
    due_date: datetime | None
    priority: str | None
    remind_at: datetime | None
    metadata_: dict | None
    created_at: datetime
    updated_at: datetime | None
