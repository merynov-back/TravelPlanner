from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.project import TravelProject


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, project: TravelProject) -> TravelProject:
        self._session.add(project)
        await self._session.flush()
        return project

    async def get_by_id(self, project_id: int) -> TravelProject | None:
        return await self._session.get(TravelProject, project_id)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        name_search: str | None = None,
        completed: bool | None = None,
    ) -> tuple[list[TravelProject], int]:
        stmt = select(TravelProject)
        count_stmt = select(func.count()).select_from(TravelProject)

        if name_search:
            pattern = f"%{name_search}%"
            stmt = stmt.where(TravelProject.name.ilike(pattern))
            count_stmt = count_stmt.where(TravelProject.name.ilike(pattern))

        if completed is not None:
            stmt = stmt.where(TravelProject.completed == completed)
            count_stmt = count_stmt.where(TravelProject.completed == completed)

        stmt = stmt.order_by(TravelProject.created_at.desc()).offset(offset).limit(limit)

        result = await self._session.execute(stmt)
        total_result = await self._session.execute(count_stmt)

        return list(result.scalars().all()), total_result.scalar_one()

    async def delete(self, project: TravelProject) -> None:
        await self._session.delete(project)
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()