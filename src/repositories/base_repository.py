from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: int) -> ModelType | None:
        return await self._session.get(self.model, id)

    async def create(self, obj: ModelType) -> ModelType:
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self._session.delete(obj)
        await self._session.flush()
