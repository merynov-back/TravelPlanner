from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.place import Place


class PlaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, place: Place) -> Place:
        self._session.add(place)
        await self._session.flush()
        return place

    async def get_by_id(self, place_id: int, project_id: int) -> Place | None:
        stmt = select(Place).where(Place.id == place_id, Place.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, project_id: int, external_place_id: str) -> Place | None:
        stmt = select(Place).where(
            Place.project_id == project_id,
            Place.external_place_id == external_place_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(
        self, project_id: int, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Place], int]:
        stmt = (
            select(Place)
            .where(Place.project_id == project_id)
            .order_by(Place.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(Place).where(Place.project_id == project_id)

        result = await self._session.execute(stmt)
        total_result = await self._session.execute(count_stmt)

        return list(result.scalars().all()), total_result.scalar_one()

    async def count_by_project(self, project_id: int) -> int:
        stmt = select(func.count()).select_from(Place).where(Place.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_all_by_project(self, project_id: int) -> list[Place]:
        stmt = select(Place).where(Place.project_id == project_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())