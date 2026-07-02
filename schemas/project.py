from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from schemas.place import PlaceCreateNested, PlaceResponse

MIN_PLACES_PER_PROJECT = 1
MAX_PLACES_PER_PROJECT = 10


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    places: list[PlaceCreateNested] = Field(default_factory=list)

    @field_validator("places")
    @classmethod
    def validate_places_count(cls, value: list[PlaceCreateNested]) -> list[PlaceCreateNested]:
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
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None


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