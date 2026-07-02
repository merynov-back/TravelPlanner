from fastapi import APIRouter, Query, status

from api.dependencies import ProjectServiceDep
from schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, service: ProjectServiceDep):
    return await service.create_project(payload)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    service: ProjectServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    name: str | None = Query(default=None, description="Search by project name"),
    completed: bool | None = Query(default=None),
):
    offset = (page - 1) * page_size
    items, total = await service.list_projects(
        offset=offset, limit=page_size, name_search=name, completed=completed
    )
    return ProjectListResponse(items=items, total=total)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: int, service: ProjectServiceDep):
    return await service.get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, payload: ProjectUpdate, service: ProjectServiceDep):
    return await service.update_project(project_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, service: ProjectServiceDep):
    await service.delete_project(project_id)