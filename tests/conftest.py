import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.dependencies.database import get_db
from src.dependencies.services import get_art_api_service
from src.exceptions import NotFoundException
from src.main import app
from src.models import Base
from src.services.art_api_service import Artwork

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
MISSING_ARTWORK_ID = "999999999"


class FakeArtService:
    """Fake Art Institute API: any numeric id exists except MISSING_ARTWORK_ID"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get_artwork(self, external_place_id: str) -> Artwork:
        self.calls.append(external_place_id)
        if external_place_id == MISSING_ARTWORK_ID:
            raise NotFoundException(
                f"Artwork with external_place_id='{external_place_id}' does not exist"
            )
        return Artwork(external_place_id=external_place_id, title=f"Artwork {external_place_id}")


@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite has foreign keys disabled by default, ON DELETE CASCADE doesn't work without this
    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

    await engine.dispose()


@pytest.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.fixture
def art_service() -> FakeArtService:
    return FakeArtService()


@pytest.fixture
async def client(session_factory, art_service):
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_art_api_service] = lambda: art_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def project(client) -> dict:
    """Project with a single unvisited place"""
    response = await client.post(
        "/projects", json={"name": "Chicago", "places": [{"external_place_id": "129884"}]}
    )
    assert response.status_code == 201
    return response.json()
