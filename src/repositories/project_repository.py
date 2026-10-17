from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.models.project import TravelProject
from src.repositories.base_repository import BaseRepository


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ProjectRepository(BaseRepository[TravelProject]):
    model = TravelProject

    async def get_with_places(self, project_id: int) -> TravelProject | None:
        stmt = (
            select(TravelProject)
            .where(TravelProject.id == project_id)
            .options(selectinload(TravelProject.places))
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(self, project_id: int) -> TravelProject | None:
        # Lock the project row so concurrent requests can't bypass the places limit
        stmt = (
            select(TravelProject)
            .where(TravelProject.id == project_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        name_search: str | None = None,
        completed: bool | None = None,
    ) -> tuple[list[TravelProject], int]:
        filters = []
        if name_search:
            filters.append(TravelProject.name.ilike(f"%{_escape_like(name_search)}%", escape="\\"))
        if completed is not None:
            filters.append(TravelProject.completed == completed)

        stmt = (
            select(TravelProject)
            .where(*filters)
            .order_by(TravelProject.created_at.desc(), TravelProject.id.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(TravelProject).where(*filters)

        result = await self._session.execute(stmt)
        total = await self._session.scalar(count_stmt)
        return list(result.scalars().all()), total or 0
