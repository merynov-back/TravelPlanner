from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import MAX_PLACES_PER_PROJECT
from src.exceptions import BusinessRuleViolation, ConflictException, NotFoundException
from src.models.place import Place
from src.models.project import TravelProject
from src.repositories.place_repository import PlaceRepository
from src.repositories.project_repository import ProjectRepository
from src.schemas.place import PlaceCreate, PlaceUpdate
from src.services.art_api_service import ArtInstituteService


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
        await self._get_project_or_404(project_id)
        await self._check_can_add(project_id, payload.external_place_id)
        # Release the connection while waiting for the external API
        await self._session.commit()

        artwork = await self._art_api.get_artwork(payload.external_place_id)

        # A concurrent request could have slipped in during the API call, so check again under the lock
        project = await self._get_project_or_404(project_id, for_update=True)
        await self._check_can_add(project_id, artwork.external_place_id)

        place = Place(
            project_id=project.id,
            external_place_id=artwork.external_place_id,
            title=artwork.title,
            notes=payload.notes,
        )
        try:
            await self._places.create(place)
        except IntegrityError as exc:
            await self._session.rollback()
            raise self._duplicate_error(artwork.external_place_id) from exc

        # The new place isn't visited, so the project is no longer completed
        project.completed = False

        await self._session.commit()
        await self._session.refresh(place)
        return place

    async def get_place(self, project_id: int, place_id: int) -> Place:
        await self._get_project_or_404(project_id)
        return await self._get_place_or_404(project_id, place_id)

    async def list_places(
        self, project_id: int, *, offset: int, limit: int
    ) -> tuple[list[Place], int]:
        await self._get_project_or_404(project_id)
        return await self._places.list_by_project(project_id, offset=offset, limit=limit)

    async def update_place(self, project_id: int, place_id: int, payload: PlaceUpdate) -> Place:
        project = await self._get_project_or_404(project_id, for_update=True)
        place = await self._get_place_or_404(project_id, place_id)

        changes = payload.model_dump(exclude_unset=True)
        visited_changed = "visited" in changes and changes["visited"] != place.visited

        for field, value in changes.items():
            setattr(place, field, value)
        await self._session.flush()

        if visited_changed:
            total, visited = await self._places.visited_stats(project_id)
            project.completed = total > 0 and total == visited

        await self._session.commit()
        await self._session.refresh(place)
        return place

    async def _check_can_add(self, project_id: int, external_place_id: str) -> None:
        if await self._places.exists_in_project(project_id, external_place_id):
            raise self._duplicate_error(external_place_id)

        if await self._places.count_by_project(project_id) >= MAX_PLACES_PER_PROJECT:
            raise BusinessRuleViolation(
                f"Project already contains the maximum of {MAX_PLACES_PER_PROJECT} places"
            )

    async def _get_project_or_404(
        self, project_id: int, *, for_update: bool = False
    ) -> TravelProject:
        if for_update:
            project = await self._projects.get_for_update(project_id)
        else:
            project = await self._projects.get_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Project with id={project_id} not found")
        return project

    async def _get_place_or_404(self, project_id: int, place_id: int) -> Place:
        place = await self._places.get_in_project(project_id, place_id)
        if place is None:
            raise NotFoundException(f"Place with id={place_id} not found in this project")
        return place

    @staticmethod
    def _duplicate_error(external_place_id: str) -> ConflictException:
        return ConflictException(
            f"Place with external_place_id='{external_place_id}' already exists in this project"
        )
