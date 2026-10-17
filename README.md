# Travel Planner API

A REST service for planning trips. Users create travel projects and fill them with places — artworks from the [Art Institute of Chicago API](https://api.artic.edu/docs/) — leave notes on them and mark them as visited. Once every place in a project is visited, the project is automatically marked as `completed`.

**Stack:** Python 3.12 · FastAPI · PostgreSQL 15 · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · HTTPX · aiocache · Docker Compose · Pytest

---

## Contents

- [Quick start](#quick-start)
- [Environment variables](#environment-variables)
- [Business rules](#business-rules)
- [API](#api)
- [Errors](#errors)
- [Local development](#local-development)
- [Tests](#tests)
- [Migrations](#migrations)
- [Project structure](#project-structure)
- [Useful commands](#useful-commands)
- [Troubleshooting](#troubleshooting)

---

## Quick start

All you need is **Docker** with Compose.

```bash
cp .env.example .env
docker compose up -d --build
```

Migrations are applied automatically when the `api` container starts.

Then open Swagger UI at http://localhost:8000/docs (ReDoc — http://localhost:8000/redoc).

| Service | Container | Address |
|---|---|---|
| `api` | `travel-api` | http://localhost:8000 |
| `postgres` | `travel` | `localhost:5544` |

---

## Environment variables

Settings are read from `.env` in the project root, see [`.env.example`](.env.example). `.env` itself is git-ignored — never commit it.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | — | Postgres credentials for Docker |
| `DATABASE_URL` | — | Database URL for running without Docker. Inside Docker it is set automatically |
| `ART_API_BASE_URL` | `https://api.artic.edu/api/v1` | Art Institute API base URL |
| `ART_API_TIMEOUT_SECONDS` | `10` | External API request timeout |
| `ART_API_CACHE_TTL_SECONDS` | `3600` | How long an artwork lookup is cached |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Business rules

- A project holds **1 to 10 places**. Places are optional on creation, but if a list is passed it must contain 1–10 items.
- The same artwork can't be added to a project twice (`409`). `external_place_id` must be a positive integer; leading zeros are stripped, so `"0129884"` and `"129884"` are the same artwork.
- Every place is validated against the Art Institute API before it is saved. Unknown artwork — `404`, API unavailable — `502`.
- A project with at least one visited place can't be deleted (`400`).
- When all places are visited, `completed` becomes `true`. Unmarking a place or adding a new one switches it back to `false`.
- `PATCH` updates only the fields that were sent. `null` in `description`, `start_date` or `notes` clears the value.

The places limit and uniqueness are safe under concurrent requests: the project row is locked with `SELECT ... FOR UPDATE` before a place is added, and the database enforces `UNIQUE (project_id, external_place_id)`.

---

## API

### Projects

| Method | Path | Description |
|---|---|---|
| `POST` | `/projects` | Create a project (optionally with a list of places) |
| `GET` | `/projects` | List projects: `page` / `page_size`, search by `name`, filter by `completed` |
| `GET` | `/projects/{id}` | Get a project with its places |
| `PATCH` | `/projects/{id}` | Update `name` / `description` / `start_date` |
| `DELETE` | `/projects/{id}` | Delete a project |

### Places

| Method | Path | Description |
|---|---|---|
| `POST` | `/projects/{project_id}/places` | Add a place |
| `GET` | `/projects/{project_id}/places` | List project places (paginated) |
| `GET` | `/projects/{project_id}/places/{place_id}` | Get a place |
| `PATCH` | `/projects/{project_id}/places/{place_id}` | Update `notes` and/or `visited` |

`GET /health` — health check.

<details>
<summary><b>curl examples</b></summary>

```bash
# Create a project with a place
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicago Art Trip",
    "start_date": "2026-08-01",
    "places": [{ "external_place_id": "129884", "notes": "Must see" }]
  }'

# Add another place
curl -X POST http://localhost:8000/projects/1/places \
  -H "Content-Type: application/json" \
  -d '{ "external_place_id": "27992" }'

# Mark a place as visited
curl -X PATCH http://localhost:8000/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{ "visited": true }'

# Search projects
curl "http://localhost:8000/projects?name=chicago&completed=false&page=1&page_size=20"
```

</details>

A ready-to-use Postman collection is in [`postman_collection.json`](postman_collection.json), including negative scenarios. The `base_url` variable defaults to `http://127.0.0.1:8000`.

---

## Errors

All errors share the same shape:

```json
{ "detail": "Project with id=42 not found" }
```

| Code | When |
|---|---|
| `400` | Business rule violation (places limit, deleting a project with visited places) |
| `404` | Project, place or artwork not found |
| `409` | Duplicate place in a project |
| `422` | Request validation error (FastAPI format, `detail` is a list) |
| `502` | Art Institute API is unavailable or returned an unexpected response |

---

## Local development

Keep Postgres in Docker and run the app locally:

```bash
docker compose up -d postgres

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head
uvicorn src.main:app --reload
```

---

## Tests

Tests run against in-memory SQLite with a fake Art Institute API, so neither Postgres nor internet access is required.

```bash
pytest -v
```

| File | Covers |
|---|---|
| `tests/test_projects_api.py` | Project endpoints |
| `tests/test_places_api.py` | Place endpoints and `completed` recalculation |
| `tests/test_art_api_service.py` | Art Institute API client: error handling, caching |

---

## Migrations

```bash
# Generate a migration after changing models
alembic revision --autogenerate -m "describe the change"

# Apply
alembic upgrade head

# Roll back the last one
alembic downgrade -1
```

Inside Docker — the same commands via `docker compose exec api ...`.

---

## Project structure

```
TravelPlanner/
├── src/
│   ├── main.py              # FastAPI app, lifespan, routers
│   ├── config.py            # Settings from .env and constants
│   ├── database.py          # Async engine and session factory
│   ├── exceptions.py        # Domain exceptions and handlers
│   ├── routers/             # HTTP endpoints, no business logic
│   ├── services/            # Business logic and the Art Institute API client
│   ├── repositories/        # Database access
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   └── dependencies/        # FastAPI dependencies (session, services)
├── migrations/              # Alembic migrations
├── tests/                   # Pytest
├── postman_collection.json
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

Request flow: **router → service → repository → DB**. Only `services/art_api_service.py` talks to the Art Institute API; a single shared HTTP client is created in the app `lifespan`.

---

## Useful commands

```bash
docker compose ps                  # container status
docker compose logs -f api         # follow API logs
docker compose up -d --build api   # rebuild the API after code changes
docker compose down                # stop everything
docker compose down -v             # stop and remove database data ⚠️
```

Connect to the database:

```bash
docker compose exec postgres psql -U postgres -d travel
```

---

## Troubleshooting

**`env file .env not found`** — create it: `cp .env.example .env`.

**`relation "travel_projects" does not exist`** — migrations weren't applied, run `alembic upgrade head`.

**`502 Failed to reach Art Institute API`** — the external API is down or there's no internet access from the container.

**Port is already in use** — change the left side of `ports` in `docker-compose.yml`, e.g. `"8001:8000"`.
