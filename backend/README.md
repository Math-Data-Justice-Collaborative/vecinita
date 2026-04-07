# Vecinita Backend (FastAPI)

This backend container builds from the repository root using `backend/Dockerfile`, copying the Python package sources from `src/`, along with `scripts/` and `tests/`.

## Local Setup (Non-Docker)

```bash
cd backend
uv sync
```

Recommended local `.env` minimum for stable startup and tests:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=test-openai-key
DEEPSEEK_API_KEY=test-deepseek-key
```

At least one LLM provider must be configured (`OLLAMA_BASE_URL`, `DEEPSEEK_API_KEY`, or `OPENAI_API_KEY`).

### Startup Preflight And Warmup

The backend now runs a startup preflight before serving requests to reduce first-request latency and catch readiness issues early.

Checks include:
- Guardrails preload (Hub validator if installed, or local fallback)
- PostgreSQL connectivity heartbeat
- Active data backend connectivity probe (`postgres`)

Configuration:

```env
BACKEND_PREFLIGHT_ENABLED=true
BACKEND_PREFLIGHT_STRICT=false
GUARDRAILS_HUB_AUTO_INSTALL=false
GUARDRAILS_PERSISTENCE_DIR=/data/cache
```

- Set `BACKEND_PREFLIGHT_STRICT=true` to fail startup when preflight is degraded.
- Set `GUARDRAILS_PERSISTENCE_DIR` to a mounted volume path (Render disk, Docker volume, Modal volume) to persist Guardrails/HuggingFace caches across restarts.
- `/health` now includes `readiness` and `preflight` details while keeping `status: ok` for compatibility with existing probes.

Run backend tests:

```bash
cd backend
uv run pytest -q
```

## Build & Run (Compose)

From the repo root:

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Healthcheck: http://localhost:8000/health

## Notes
- Dockerfile uses Playwright Python base to support scraping and browser automation.
- Dependencies install via `pyproject.toml` with the `embedding` extra.
- App entrypoint: `uvicorn src.agent.main:app --host 0.0.0.0 --port 8000`.
- If you later move `src/`, `scripts/`, and `tests/` into `backend/`, you can change the compose build `context` to `./backend` and keep the same Dockerfile.

## Streaming Regression Checks

Use the CI-safe streaming regression alias to run streaming tests while ignoring known unrelated scraper import blockers:

```bash
cd backend
make test-streaming-ci
```

Equivalent explicit pytest command:

```bash
uv run pytest -m streaming -q \
	--ignore=tests/test_scraper_advanced.py \
	--ignore=tests/test_scraper_upload_chunks.py \
	--ignore=tests/test_services/scraper/test_scraper_advanced.py \
	--ignore=tests/test_services/scraper/test_scraper_upload_chunks.py
```
