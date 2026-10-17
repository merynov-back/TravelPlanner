from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.config import MAX_PLACES_PER_PROJECT, MIN_PLACES_PER_PROJECT
from src.schemas.place import PlaceCreate, PlaceResponse


class ProjectCreate(BaseModel):
    """Create a project, places can be passed right away"""
    name: str = Field(..., min_length=1, max_length=255, examples=["Chicago Art Trip"])
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    places: list[PlaceCreate] = Field(default_factory=list)

    @field_validator("places")
    @classmethod
    def validate_places(cls, value: list[PlaceCreate]) -> list[PlaceCreate]:
        if value and not (MIN_PLACES_PER_PROJECT <= len(value) <= MAX_PLACES_PER_PROJECT):
            raise ValueError(
                f"A project must contain between {MIN_PLACES_PER_PROJECT} "
                f"and {MAX_PLACES_PER_PROJECT} places"
            )
        external_ids = [p.external_place_id for p in value]
        if len(external_ids) != len(set(external_ids)):
            raise ValueError("Duplicate external_place_id found in the request")
        return value


class ProjectUpdate(BaseModel):
    """Partial project update. null in description/start_date clears the field"""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None

    @field_validator("name")
    @classmethod
    def name_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("name cannot be null")
        return value


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    start_date: date | None
    completed: bool
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    places: list[PlaceResponse] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
