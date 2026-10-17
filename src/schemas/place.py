from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlaceCreate(BaseModel):
    """Add a place (an Art Institute of Chicago artwork) to a project"""
    external_place_id: str = Field(..., min_length=1, max_length=100, examples=["129884"])
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("external_place_id", mode="before")
    @classmethod
    def normalize_external_id(cls, value: str | int) -> str:
        # "0129884" and "129884" are the same artwork, so store it without leading zeros
        value = str(value).strip()
        if not value.isdigit():
            raise ValueError("external_place_id must be a positive integer")
        return str(int(value))


class PlaceUpdate(BaseModel):
    """Update notes and/or the visited flag"""
    notes: str | None = Field(default=None, max_length=2000)
    visited: bool | None = None

    @field_validator("visited")
    @classmethod
    def visited_not_null(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("visited cannot be null")
        return value


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
