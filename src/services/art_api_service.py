import logging
from dataclasses import dataclass

import httpx
from aiocache import cached

from src.config import settings
from src.exceptions import ExternalServiceError, NotFoundException

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Artwork:
    external_place_id: str
    title: str


class ArtInstituteService:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @cached(ttl=settings.ART_API_CACHE_TTL_SECONDS, noself=True)
    async def get_artwork(self, external_place_id: str) -> Artwork:
        try:
            response = await self._client.get(
                f"/artworks/{external_place_id}", params={"fields": "id,title"}
            )
        except httpx.RequestError as exc:
            logger.warning("Art Institute API is unreachable: %r", exc)
            raise ExternalServiceError("Failed to reach Art Institute API") from exc

        if response.status_code == httpx.codes.NOT_FOUND:
            raise NotFoundException(
                f"Artwork with external_place_id='{external_place_id}' does not exist"
            )

        if response.status_code != httpx.codes.OK:
            logger.warning(
                "Art Institute API returned %s for artwork %s",
                response.status_code,
                external_place_id,
            )
            raise ExternalServiceError(
                f"Art Institute API returned unexpected status {response.status_code}"
            )

        try:
            data = response.json().get("data")
        except ValueError as exc:
            raise ExternalServiceError("Art Institute API returned invalid JSON") from exc

        if not isinstance(data, dict) or "id" not in data:
            raise NotFoundException(
                f"Artwork with external_place_id='{external_place_id}' does not exist"
            )

        return Artwork(
            external_place_id=str(data["id"]),
            title=data.get("title") or "Untitled",
        )


def create_art_api_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.ART_API_BASE_URL,
        timeout=settings.ART_API_TIMEOUT_SECONDS,
    )
