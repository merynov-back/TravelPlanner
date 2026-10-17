from sqlalchemy import case, exists, func, select

from src.models.place import Place
from src.repositories.base_repository import BaseRepository


class PlaceRepository(BaseRepository[Place]):
    model = Place

    async def get_in_project(self, project_id: int, place_id: int) -> Place | None:
        stmt = select(Place).where(Place.id == place_id, Place.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_in_project(self, project_id: int, external_place_id: str) -> bool:
        stmt = select(
            exists().where(
                Place.project_id == project_id,
                Place.external_place_id == external_place_id,
            )
        )
        return bool(await self._session.scalar(stmt))

    async def list_by_project(
        self, project_id: int, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Place], int]:
        stmt = (
            select(Place)
            .where(Place.project_id == project_id)
            .order_by(Place.created_at.desc(), Place.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        total = await self.count_by_project(project_id)
        return list(result.scalars().all()), total

    async def count_by_project(self, project_id: int) -> int:
        stmt = select(func.count()).select_from(Place).where(Place.project_id == project_id)
        return await self._session.scalar(stmt) or 0

    async def visited_stats(self, project_id: int) -> tuple[int, int]:
        """Returns (total places, visited places)"""
        stmt = select(
            func.count(Place.id),
            func.coalesce(func.sum(case((Place.visited.is_(True), 1), else_=0)), 0),
        ).where(Place.project_id == project_id)
        total, visited = (await self._session.execute(stmt)).one()
        return total, visited

    async def has_visited(self, project_id: int) -> bool:
        stmt = select(exists().where(Place.project_id == project_id, Place.visited.is_(True)))
        return bool(await self._session.scalar(stmt))
