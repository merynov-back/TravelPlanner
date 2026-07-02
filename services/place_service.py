from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import BusinessRuleViolation, ConflictException, NotFoundException
from models.place import Place
from repositories.place_repository import PlaceRepository
from repositories.project_repository import ProjectRepository
from schemas.place import PlaceCreate, PlaceUpdate
from services.art_api_service import ArtInstituteService

MAX_PLACES_PER_PROJECT = 10


class PlaceService:
    def __init__(
        self,
        session: AsyncSession,
        place_repository: PlaceRepository,
        project_repository: ProjectRepository,
        art_api_service: ArtInstituteService,
    ) -> None:
        self._session = session
        self._places = place_repository
        self._projects = project_repository
        self._art_api = art_api_service

    async def add_place(self, project_id: int, payload: PlaceCreate) -> Place:
        project = await self._get_project_or_404(project_id)

        existing = await self._places.get_by_external_id(project_id, payload.external_place_id)
        if existing is not None:
            raise ConflictException(
                f"Place with external_place_id='{payload.external_place_id}' "
                "already exists in this project"
            )

        current_count = await self._places.count_by_project(project_id)
        if current_count >= MAX_PLACES_PER_PROJECT:
            raise BusinessRuleViolation(
                f"Project already contains the maximum of {MAX_PLACES_PER_PROJECT} places"
            )

        artwork = await self._art_api.get_artwork(payload.external_place_id)

        place = Place(
            project_id=project.id,
            external_place_id=artwork["external_place_id"],
            title=artwork["title"],
            notes=payload.notes,
        )
        place = await self._places.create(place)
        await self._session.commit()
        await self._session.refresh(place)
        return place

    async def get_place(self, project_id: int, place_id: int) -> Place:
        await self._get_project_or_404(project_id)
        place = await self._places.get_by_id(place_id, project_id)
        if place is None:
            raise NotFoundException(f"Place with id={place_id} not found in this project")
        return place

    async def list_places(
        self, project_id: int, *, offset: int, limit: int
    ) -> tuple[list[Place], int]:
        await self._get_project_or_404(project_id)
        return await self._places.list_by_project(project_id, offset=offset, limit=limit)

    async def update_place(self, project_id: int, place_id: int, payload: PlaceUpdate) -> Place:
        place = await self.get_place(project_id, place_id)

        if payload.notes is not None:
            place.notes = payload.notes

        visited_changed = payload.visited is not None and payload.visited != place.visited
        if payload.visited is not None:
            place.visited = payload.visited

        await self._session.flush()

        if visited_changed:
            await self._recalculate_project_completion(project_id)

        await self._session.commit()
        await self._session.refresh(place)
        return place

    async def _recalculate_project_completion(self, project_id: int) -> None:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            return

        all_places = await self._places.list_all_by_project(project_id)
        project.completed = bool(all_places) and all(p.visited for p in all_places)
        await self._session.flush()

    async def _get_project_or_404(self, project_id: int):
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Project with id={project_id} not found")
        return project