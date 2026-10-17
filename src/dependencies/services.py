from typing import Annotated

from fastapi import Depends, Request

from src.dependencies.database import DbSession
from src.repositories.place_repository import PlaceRepository
from src.repositories.project_repository import ProjectRepository
from src.services.art_api_service import ArtInstituteService
from src.services.place_service import PlaceService
from src.services.project_service import ProjectService


def get_art_api_service(request: Request) -> ArtInstituteService:
    return ArtInstituteService(request.app.state.art_api_client)


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
