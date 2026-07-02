from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from repositories.place_repository import PlaceRepository
from repositories.project_repository import ProjectRepository
from services.art_api_service import ArtInstituteService, art_institute_service
from services.place_service import PlaceService
from services.project_service import ProjectService

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_art_api_service() -> ArtInstituteService:
    return art_institute_service


def get_project_repository(session: DbSession) -> ProjectRepository:
    return ProjectRepository(session)


def get_place_repository(session: DbSession) -> PlaceRepository:
    return PlaceRepository(session)


def get_project_service(
    session: DbSession,
    project_repository: Annotated[ProjectRepository, Depends(get_project_repository)],
    place_repository: Annotated[PlaceRepository, Depends(get_place_repository)],
    art_api_service: Annotated[ArtInstituteService, Depends(get_art_api_service)],
) -> ProjectService:
    return ProjectService(session, project_repository, place_repository, art_api_service)


def get_place_service(
    session: DbSession,
    place_repository: Annotated[PlaceRepository, Depends(get_place_repository)],
    project_repository: Annotated[ProjectRepository, Depends(get_project_repository)],
    art_api_service: Annotated[ArtInstituteService, Depends(get_art_api_service)],
) -> PlaceService:
    return PlaceService(session, place_repository, project_repository, art_api_service)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
PlaceServiceDep = Annotated[PlaceService, Depends(get_place_service)]