import httpx
import pytest

from src.exceptions import ExternalServiceError, NotFoundException
from src.services.art_api_service import ArtInstituteService


@pytest.fixture(autouse=True)
async def clear_cache():
    await ArtInstituteService.get_artwork.cache.clear()
    yield
    await ArtInstituteService.get_artwork.cache.clear()


def make_service(handler) -> ArtInstituteService:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.test/api/v1"
    )
    return ArtInstituteService(client)


async def test_returns_artwork():
    service = make_service(
        lambda request: httpx.Response(200, json={"data": {"id": 129884, "title": "Starry Night"}})
    )

    artwork = await service.get_artwork("129884")

    assert artwork.external_place_id == "129884"
    assert artwork.title == "Starry Night"


async def test_result_is_cached():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"data": {"id": 1, "title": "A"}})

    service = make_service(handler)
    await service.get_artwork("1")
    await service.get_artwork("1")

    assert len(calls) == 1


async def test_404_raises_not_found():
    service = make_service(lambda request: httpx.Response(404))

    with pytest.raises(NotFoundException):
        await service.get_artwork("1")


async def test_server_error_raises_external_error():
    service = make_service(lambda request: httpx.Response(503))

    with pytest.raises(ExternalServiceError):
        await service.get_artwork("1")


async def test_unexpected_payload_raises_not_found():
    service = make_service(lambda request: httpx.Response(200, json={"data": [{"id": 1}]}))

    with pytest.raises(NotFoundException):
        await service.get_artwork("1")


async def test_invalid_json_raises_external_error():
    service = make_service(lambda request: httpx.Response(200, text="<html>"))

    with pytest.raises(ExternalServiceError):
        await service.get_artwork("1")


async def test_network_error_raises_external_error():
    def handler(request):
        raise httpx.ConnectError("boom")

    service = make_service(handler)

    with pytest.raises(ExternalServiceError):
        await service.get_artwork("1")
