import httpx
from aiocache import cached
from aiocache.serializers import JsonSerializer

from core.exceptions import ExternalServiceError, NotFoundException

ART_INSTITUTE_BASE_URL = "https://api.artic.edu/api/v1/artworks"
REQUEST_TIMEOUT_SECONDS = 10.0
CACHE_TTL_SECONDS = 3600


class ArtInstituteService:

    @cached(ttl=CACHE_TTL_SECONDS, serializer=JsonSerializer())
    async def get_artwork(self, external_place_id: str) -> dict:
        url = f"{ART_INSTITUTE_BASE_URL}/{external_place_id}"

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(url)
        except httpx.RequestError as exc:
            raise ExternalServiceError(
                f"Failed to reach Art Institute API: {exc}"
            ) from exc

        if response.status_code == httpx.codes.NOT_FOUND:
            raise NotFoundException(
                f"Artwork with external_place_id='{external_place_id}' does not exist"
            )

        if response.status_code != httpx.codes.OK:
            raise ExternalServiceError(
                f"Art Institute API returned unexpected status {response.status_code}"
            )

        payload = response.json()
        data = payload.get("data")

        if not data:
            raise NotFoundException(
                f"Artwork with external_place_id='{external_place_id}' does not exist"
            )

        return {
            "external_place_id": str(data["id"]),
            "title": data.get("title", "Untitled"),
        }


art_institute_service = ArtInstituteService()