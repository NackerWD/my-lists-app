import uuid

from pydantic import BaseModel, ConfigDict


class ListTypeBase(BaseModel):
    slug: str
    label: str
    icon: str | None = None
    is_active: bool = True


class ListTypeCreate(ListTypeBase):
    pass


class ListTypeUpdate(BaseModel):
    label: str | None = None
    icon: str | None = None
    is_active: bool | None = None


class ListTypeResponse(ListTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
