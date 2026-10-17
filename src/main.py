import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.database import engine
from src.exceptions import register_exception_handlers
from src.routers import places, projects
from src.services.art_api_service import create_art_api_client

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.art_api_client = create_art_api_client()
    yield
    await app.state.art_api_client.aclose()
    await engine.dispose()


app = FastAPI(title="Travel Planner API", version="1.0.0", lifespan=lifespan)

register_exception_handlers(app)

app.include_router(projects.router)
app.include_router(places.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
