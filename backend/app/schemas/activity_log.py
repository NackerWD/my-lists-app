import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogBase(BaseModel):
    action: str
    payload: dict | None = None


class ActivityLogCreate(ActivityLogBase):
    list_id: uuid.UUID
    user_id: uuid.UUID | None = None


class ActivityLogResponse(ActivityLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_id: uuid.UUID
    user_id: uuid.UUID | None
    created_at: datetime
