from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaceBase(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class PlaceCreate(BaseModel):
    external_place_id: str = Field(..., min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)


class PlaceCreateNested(PlaceCreate):
    """Used when places are provided inline during project creation"""


class PlaceUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)
    visited: bool | None = None


class PlaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    external_place_id: str
    title: str
    notes: str | None
    visited: bool
    created_at: datetime
    updated_at: datetime


class PlaceListResponse(BaseModel):
    items: list[PlaceResponse]
    total: int