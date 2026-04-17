import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DeviceTokenBase(BaseModel):
    token: str
    platform: Literal["ios", "android", "web"]


class DeviceTokenCreate(DeviceTokenBase):
    pass


class DeviceTokenResponse(DeviceTokenBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
