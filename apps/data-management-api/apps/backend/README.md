# Data-management API (FastAPI)

Operator-facing HTTP service for the data-management SPA: **scrape job paths** proxy to the
configured scraper base URL via `service_clients.ScraperClient` (including Modal-backed
`GET /health` when `MODAL_FUNCTION_INVOCATION` is enabled), and **`POST /embed`** / **`POST /predict`**
delegate to `EmbeddingClient` and `ModelClient` for ingest-style calls (**feature 007** tasks **T017** / **T018**).

## Run locally (from vecinita monorepo root)

```bash
make dev-data-management-api
```

Or manually (same `PYTHONPATH` as CI):

```bash
cd backend
PYTHONPATH=../apis/data-management-api/apps/backend:../apis/data-management-api/packages/service-clients:../apis/data-management-api/packages/shared-schemas:../apis/data-management-api/packages/shared-config \
  uv run python -m uvicorn vecinita_dm_api.app:create_app --factory --host 0.0.0.0 --port 8005
```

Configure downstream URLs via `SCRAPER_SERVICE_BASE_URL`, `EMBEDDING_SERVICE_BASE_URL`, and
`MODEL_SERVICE_BASE_URL` (see `packages/shared-config`).

## Layout

- `pyproject.toml` — app metadata; runtime deps include `fastapi`, `uvicorn`, `httpx`, `modal`.
- `vecinita_dm_api/` — `create_app()` factory and routers (`/health`, `/jobs`, `/embed`, `/predict`).
