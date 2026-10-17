from fastapi import APIRouter, Query, status

from src.dependencies.services import PlaceServiceDep
from src.schemas.place import PlaceCreate, PlaceListResponse, PlaceResponse, PlaceUpdate

router = APIRouter(prefix="/projects/{project_id}/places", tags=["places"])


@router.post(
    "",
    response_model=PlaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a place to a project",
)
async def add_place(project_id: int, payload: PlaceCreate, service: PlaceServiceDep):
    return await service.add_place(project_id, payload)


@router.get("", response_model=PlaceListResponse, summary="List project places")
async def list_places(
    project_id: int,
    service: PlaceServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    items, total = await service.list_places(project_id, offset=offset, limit=page_size)
    return PlaceListResponse(items=items, total=total)


@router.get("/{place_id}", response_model=PlaceResponse, summary="Get a place")
async def get_place(project_id: int, place_id: int, service: PlaceServiceDep):
    return await service.get_place(project_id, place_id)


@router.patch("/{place_id}", response_model=PlaceResponse, summary="Update notes / mark as visited")
async def update_place(
    project_id: int, place_id: int, payload: PlaceUpdate, service: PlaceServiceDep
):
    return await service.update_place(project_id, place_id, payload)
