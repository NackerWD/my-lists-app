import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ListItemCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str
    due_date: datetime | None = None
    priority: Literal["high", "medium", "low"] | None = None
    remind_at: datetime | None = None
    position: int = 0
    metadata_: dict | None = Field(
        default=None,
        serialization_alias="metadata",
        validation_alias="metadata",
    )


class ListItemUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str | None = None
    is_checked: bool | None = None
    position: int | None = None
    due_date: datetime | None = None
    priority: Literal["high", "medium", "low"] | None = None
    remind_at: datetime | None = None
    metadata_: dict | None = Field(
        default=None,
        serialization_alias="metadata",
        validation_alias="metadata",
    )


class ListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)

    id: uuid.UUID
    list_id: uuid.UUID
    created_by: uuid.UUID | None
    content: str
    is_checked: bool
    position: int
    due_date: datetime | None
    priority: str | None
    remind_at: datetime | None
    reminded_at: datetime | None = None
    metadata_: dict | None = Field(default=None, serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime | None
