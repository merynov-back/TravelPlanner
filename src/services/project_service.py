import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import BusinessRuleViolation, NotFoundException
from src.models.place import Place
from src.models.project import TravelProject
from src.repositories.place_repository import PlaceRepository
from src.repositories.project_repository import ProjectRepository
from src.schemas.project import ProjectCreate, ProjectUpdate
from src.services.art_api_service import ArtInstituteService


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
        # Validate all places against the external API before touching the DB
        artworks = await asyncio.gather(
            *(self._art_api.get_artwork(p.external_place_id) for p in payload.places)
        )

        project = TravelProject(
            name=payload.name,
            description=payload.description,
            start_date=payload.start_date,
            places=[
                Place(
                    external_place_id=artwork.external_place_id,
                    title=artwork.title,
                    notes=place_payload.notes,
                )
                for place_payload, artwork in zip(payload.places, artworks)
            ],
        )
        await self._projects.create(project)
        await self._session.commit()

        return await self.get_project(project.id)

    async def get_project(self, project_id: int) -> TravelProject:
        project = await self._projects.get_with_places(project_id)
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
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Project with id={project_id} not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)

        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def delete_project(self, project_id: int) -> None:
        project = await self._projects.get_for_update(project_id)
        if project is None:
            raise NotFoundException(f"Project with id={project_id} not found")

        if await self._places.has_visited(project_id):
            raise BusinessRuleViolation(
                "Cannot delete a project that has at least one visited place"
            )

        await self._projects.delete(project)
        await self._session.commit()
