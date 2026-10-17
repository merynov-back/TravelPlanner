from tests.conftest import MISSING_ARTWORK_ID


class TestCreateProject:
    async def test_create_with_places(self, client):
        response = await client.post(
            "/projects",
            json={
                "name": "Chicago Art Trip",
                "start_date": "2026-08-01",
                "places": [{"external_place_id": "129884", "notes": "Must see"}],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["completed"] is False
        assert len(data["places"]) == 1
        assert data["places"][0]["title"] == "Artwork 129884"
        assert data["places"][0]["notes"] == "Must see"

    async def test_create_without_places(self, client):
        response = await client.post("/projects", json={"name": "Empty"})

        assert response.status_code == 201
        assert response.json()["places"] == []

    async def test_more_than_ten_places_returns_422(self, client):
        places = [{"external_place_id": str(i)} for i in range(1, 12)]
        response = await client.post("/projects", json={"name": "Too many", "places": places})

        assert response.status_code == 422

    async def test_duplicates_after_normalization_return_422(self, client):
        response = await client.post(
            "/projects",
            json={
                "name": "Dup",
                "places": [{"external_place_id": "129884"}, {"external_place_id": "0129884"}],
            },
        )

        assert response.status_code == 422

    async def test_missing_artwork_returns_404_and_nothing_saved(self, client):
        response = await client.post(
            "/projects",
            json={"name": "Broken", "places": [{"external_place_id": MISSING_ARTWORK_ID}]},
        )

        assert response.status_code == 404
        assert (await client.get("/projects")).json()["total"] == 0


class TestListProjects:
    async def test_search_by_name_and_filter(self, client):
        await client.post("/projects", json={"name": "Chicago trip"})
        await client.post("/projects", json={"name": "Paris"})

        response = await client.get("/projects", params={"name": "chic", "completed": False})

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Chicago trip"

    async def test_search_escapes_like_wildcards(self, client):
        await client.post("/projects", json={"name": "Trip"})

        response = await client.get("/projects", params={"name": "%"})

        assert response.json()["total"] == 0

    async def test_pagination(self, client):
        for i in range(3):
            await client.post("/projects", json={"name": f"P{i}"})

        response = await client.get("/projects", params={"page": 2, "page_size": 2})

        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "P0"


class TestUpdateProject:
    async def test_partial_update(self, client, project):
        response = await client.patch(f"/projects/{project['id']}", json={"description": "New"})

        assert response.status_code == 200
        assert response.json()["description"] == "New"
        assert response.json()["name"] == "Chicago"

    async def test_null_clears_optional_fields(self, client):
        created = (
            await client.post(
                "/projects",
                json={"name": "P", "description": "text", "start_date": "2026-08-01"},
            )
        ).json()

        response = await client.patch(
            f"/projects/{created['id']}", json={"description": None, "start_date": None}
        )

        assert response.json()["description"] is None
        assert response.json()["start_date"] is None

    async def test_null_name_returns_422(self, client, project):
        response = await client.patch(f"/projects/{project['id']}", json={"name": None})

        assert response.status_code == 422

    async def test_unknown_project_returns_404(self, client):
        response = await client.patch("/projects/999", json={"name": "X"})

        assert response.status_code == 404


class TestDeleteProject:
    async def test_delete(self, client, project):
        response = await client.delete(f"/projects/{project['id']}")

        assert response.status_code == 204
        assert (await client.get(f"/projects/{project['id']}")).status_code == 404

    async def test_cannot_delete_with_visited_place(self, client, project):
        place_id = project["places"][0]["id"]
        await client.patch(f"/projects/{project['id']}/places/{place_id}", json={"visited": True})

        response = await client.delete(f"/projects/{project['id']}")

        assert response.status_code == 400
