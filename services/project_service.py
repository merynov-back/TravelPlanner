from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions import BusinessRuleViolation, ConflictException, NotFoundException
from models.place import Place
from models.project import TravelProject
from repositories.place_repository import PlaceRepository
from repositories.project_repository import ProjectRepository
from schemas.project import ProjectCreate, ProjectUpdate
from services.art_api_service import ArtInstituteService


class ProjectService:
    def __init__(
        self,
        session: AsyncSession,
        project_repository: ProjectRepository,
        place_repository: PlaceRepository,
        art_api_service: ArtInstituteService,
    ) -> None:
        self._session = session
        self._projects = project_repository
        self._places = place_repository
        self._art_api = art_api_service

    async def create_project(self, payload: ProjectCreate) -> TravelProject:
        project = TravelProject(
            name=payload.name,
            description=payload.description,
            start_date=payload.start_date,
        )
        project = await self._projects.create(project)

        for place_payload in payload.places:
            artwork = await self._art_api.get_artwork(place_payload.external_place_id)
            place = Place(
                project_id=project.id,
                external_place_id=artwork["external_place_id"],
                title=artwork["title"],
                notes=place_payload.notes,
            )
            await self._places.create(place)

        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def get_project(self, project_id: int) -> TravelProject:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Project with id={project_id} not found")
        return project

    async def list_projects(
        self,
        *,
        offset: int,
        limit: int,
        name_search: str | None = None,
        completed: bool | None = None,
    ) -> tuple[list[TravelProject], int]:
        return await self._projects.list(
            offset=offset,
            limit=limit,
            name_search=name_search,
            completed=completed,
        )

    async def update_project(self, project_id: int, payload: ProjectUpdate) -> TravelProject:
        project = await self.get_project(project_id)

        if payload.name is not None:
            project.name = payload.name
        if payload.description is not None:
            project.description = payload.description
        if payload.start_date is not None:
            project.start_date = payload.start_date

        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def delete_project(self, project_id: int) -> None:
        project = await self.get_project(project_id)

        places = await self._places.list_all_by_project(project_id)
        if any(place.visited for place in places):
            raise BusinessRuleViolation(
                "Cannot delete a project that has at least one visited place"
            )

        await self._projects.delete(project)
        await self._session.commit()