from fastapi import FastAPI

from api.routes import places, projects
from core.exceptions import register_exception_handlers

app = FastAPI(title="Travel Planner API", version="1.0.0")

register_exception_handlers(app)

app.include_router(projects.router)
app.include_router(places.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}