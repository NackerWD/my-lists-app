import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ListItemBase(BaseModel):
    content: str
    is_checked: bool = False
    position: int = 0
    due_date: datetime | None = None
    priority: Literal["high", "medium", "low"] | None = None
    remind_at: datetime | None = None
    metadata_: dict | None = None


class ListItemCreate(ListItemBase):
    pass


class ListItemUpdate(BaseModel):
    content: str | None = None
    is_checked: bool | None = None
    position: int | None = None
    due_date: datetime | None = None
    priority: Literal["high", "medium", "low"] | None = None
    remind_at: datetime | None = None
    metadata_: dict | None = None


class ListItemResponse(ListItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
