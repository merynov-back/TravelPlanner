from tests.conftest import MISSING_ARTWORK_ID


def places_url(project: dict) -> str:
    return f"/projects/{project['id']}/places"


class TestAddPlace:
    async def test_add_place(self, client, project):
        response = await client.post(places_url(project), json={"external_place_id": "27992"})

        assert response.status_code == 201
        assert response.json()["visited"] is False

    async def test_duplicate_returns_409(self, client, project):
        response = await client.post(places_url(project), json={"external_place_id": "129884"})

        assert response.status_code == 409

    async def test_duplicate_with_leading_zero_returns_409(self, client, project):
        response = await client.post(places_url(project), json={"external_place_id": "0129884"})

        assert response.status_code == 409

    async def test_non_numeric_id_returns_422(self, client, project, art_service):
        for bad_id in ["abc", "search?q=cat", "1/../2", "-5"]:
            response = await client.post(places_url(project), json={"external_place_id": bad_id})
            assert response.status_code == 422, bad_id

        assert art_service.calls == ["129884"]

    async def test_missing_artwork_returns_404(self, client, project):
        response = await client.post(
            places_url(project), json={"external_place_id": MISSING_ARTWORK_ID}
        )

        assert response.status_code == 404

    async def test_limit_of_ten_places(self, client, project):
        for i in range(1, 10):
            response = await client.post(places_url(project), json={"external_place_id": str(i)})
            assert response.status_code == 201

        response = await client.post(places_url(project), json={"external_place_id": "100"})

        assert response.status_code == 400

    async def test_unknown_project_returns_404(self, client):
        response = await client.post("/projects/999/places", json={"external_place_id": "1"})

        assert response.status_code == 404

    async def test_adding_place_resets_completed(self, client, project):
        place_id = project["places"][0]["id"]
        await client.patch(f"{places_url(project)}/{place_id}", json={"visited": True})
        assert (await client.get(f"/projects/{project['id']}")).json()["completed"] is True

        await client.post(places_url(project), json={"external_place_id": "27992"})

        assert (await client.get(f"/projects/{project['id']}")).json()["completed"] is False


class TestUpdatePlace:
    async def test_mark_visited_completes_project(self, client, project):
        place_id = project["places"][0]["id"]

        response = await client.patch(f"{places_url(project)}/{place_id}", json={"visited": True})

        assert response.json()["visited"] is True
        assert (await client.get(f"/projects/{project['id']}")).json()["completed"] is True

    async def test_unmark_visited_reopens_project(self, client, project):
        url = f"{places_url(project)}/{project['places'][0]['id']}"
        await client.patch(url, json={"visited": True})

        await client.patch(url, json={"visited": False})

        assert (await client.get(f"/projects/{project['id']}")).json()["completed"] is False

    async def test_not_all_visited_keeps_project_open(self, client, project):
        await client.post(places_url(project), json={"external_place_id": "27992"})

        await client.patch(
            f"{places_url(project)}/{project['places'][0]['id']}", json={"visited": True}
        )

        assert (await client.get(f"/projects/{project['id']}")).json()["completed"] is False

    async def test_notes_can_be_cleared(self, client, project):
        url = f"{places_url(project)}/{project['places'][0]['id']}"
        await client.patch(url, json={"notes": "hi"})

        response = await client.patch(url, json={"notes": None})

        assert response.json()["notes"] is None

    async def test_null_visited_returns_422(self, client, project):
        url = f"{places_url(project)}/{project['places'][0]['id']}"

        response = await client.patch(url, json={"visited": None})

        assert response.status_code == 422

    async def test_place_from_other_project_returns_404(self, client, project):
        other = (await client.post("/projects", json={"name": "Other"})).json()

        response = await client.get(f"/projects/{other['id']}/places/{project['places'][0]['id']}")

        assert response.status_code == 404


class TestListPlaces:
    async def test_list_with_pagination(self, client, project):
        await client.post(places_url(project), json={"external_place_id": "27992"})

        response = await client.get(places_url(project), params={"page_size": 1})

        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 1
