# Travel Planner API

A CRUD service for planning travel trips. Users create travel projects and
populate them with places (artworks) fetched from the **Art Institute of
Chicago API**, attach notes to places, and mark them as visited. Once every
place in a project is visited, the project is automatically marked as
`completed`.

## Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL 15
- SQLAlchemy 2.0 (async, declarative style)
- Alembic (migrations)
- Pydantic v2
- HTTPX (third-party API client)
- aiocache (caching of external API responses)

## Architecture

```
api/          -> FastAPI routes, transport layer only (no business logic)
services/     -> business logic (limits, duplicates, auto-completion, external API integration)
repositories/ -> pure database access, no business logic
models/       -> SQLAlchemy ORM models
schemas/      -> Pydantic request/response schemas
core/         -> settings, domain exceptions
db/           -> declarative base, async engine/session
migrations/   -> Alembic
```

Call flow: **route → service → repository → DB**. HTTP calls to the Art
Institute of Chicago API are encapsulated in `services/art_api_service.py`
and are never made directly from routes or repositories.

## Business Rules

- A project contains between 1 and 10 places (when created with a nested
  list of places).
- The same `external_place_id` cannot appear twice within the same project
  (enforced both at the service layer and via a `UNIQUE` constraint in the
  database).
- Before a place is added, its existence is validated through the Art
  Institute of Chicago API (`GET /artworks/{id}`). If the artwork does not
  exist — `404`.
- Deleting a project is forbidden if at least one of its places is marked
  `visited=true` (`400`).
- As soon as every place in a project is marked `visited=true`,
  `project.completed` automatically becomes `true`. Unmarking a place
  re-triggers the recalculation.

## Getting Started

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts Postgres 15 on `localhost:5544`, database `travel`.

### 2. Set up the environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5544/travel
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Run the application

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive documentation (Swagger UI): `http://127.0.0.1:8000/docs`.

## Endpoints

### Travel Projects

| Method | Path              | Description                                                          |
|--------|-------------------|------------------------------------------------------------------------|
| POST   | `/projects`       | Create a project (optionally with a list of places in one request)   |
| GET    | `/projects`       | List projects (pagination, search by name, filter by `completed`)    |
| GET    | `/projects/{id}`  | Get a single project with its places                                 |
| PATCH  | `/projects/{id}`  | Update `name` / `description` / `start_date`                         |
| DELETE | `/projects/{id}`  | Delete a project (forbidden if it has any visited places)            |

### Places

| Method | Path                                          | Description                                    |
|--------|------------------------------------------------|-------------------------------------------------|
| POST   | `/projects/{project_id}/places`                | Add a place to a project (validated via Art Institute API) |
| GET    | `/projects/{project_id}/places`                | List a project's places (pagination)           |
| GET    | `/projects/{project_id}/places/{place_id}`     | Get a single place                              |
| PATCH  | `/projects/{project_id}/places/{place_id}`     | Update `notes` and/or `visited`                 |

## Example Requests

Create a project with places:

```bash
curl -X POST http://127.0.0.1:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicago Art Trip",
    "description": "Weekend at the Art Institute",
    "start_date": "2026-08-01",
    "places": [
      { "external_place_id": "129884", "notes": "Must see" }
    ]
  }'
```

Mark a place as visited:

```bash
curl -X PATCH http://127.0.0.1:8000/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{ "visited": true }'
```

## Postman Collection

`postman_collection.json` in the repository root covers all endpoints,
including negative scenarios (duplicate `external_place_id`, exceeding the
10-place limit, deleting a project with a visited place, a non-existent
artwork). Import it into Postman via `File → Import →
postman_collection.json`.

The collection variable `base_url` defaults to `http://127.0.0.1:8000`.

## Possible Improvements

- Authentication (JWT / API key) — endpoints are currently open.
- Idempotency safeguards for repeated `POST /places` calls (currently only
  protected against duplicate `external_place_id` within the same project).
- API-level rate limiting.
- More resilient caching for the Art Institute API — currently an in-memory
  `aiocache` backend; a Redis backend would be needed for multiple app
  instances.
- Unit and integration tests (pytest + `httpx.AsyncClient` + a test
  database).
- Structured logging (not yet wired up).
