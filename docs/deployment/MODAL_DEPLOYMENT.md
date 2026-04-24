# Modal Deployment Guide

## Overview

Vecinita deploys several Modal-backed workloads:
- **Embedding Service**: Generates text embeddings using sentence-transformers
- **Model Service**: Serves Ollama-compatible chat (default **`gemma3`**); CPU-class workers (no GPU requirement in the current app definition)
- **Scraper Service**: Scrapes and re-indexes content (HTTP entrypoints plus scheduled jobs where configured)

## Architecture

```
Frontend (React)
    ↓
API Gateway (FastAPI @ :8004)
    ├── Q&A Router → Agent Service (LangGraph @ :8000)
    ├── Embed Router → Modal Embedding Service
    ├── Scrape Router → Backend + Modal Scraper Service
    └── Ask Router → Question answering

Modal Services (representative layout; exact app names follow your Modal workspace):
├── vecinita-embedding (Modal **Functions** only)
│   └── ``embed_query``, ``embed_batch`` — invoke via ``modal.Function.from_name`` (gateway: ``MODAL_FUNCTION_INVOCATION``) or ``modal run ...::embed_query.remote(...)``
│
├── vecinita-model (Modal **Functions** only)
│   └── ``chat_completion``, ``download_model``, ``download_default_model`` — no Modal-hosted Ollama HTTP app; local HTTP remains available via Docker ``vecinita.asgi`` if you need it
│
├── vecinita-scraper (workers + queues)
│   └── Modal ``@app.function`` workers (``drain_*_queue``, ``trigger_reindex``, …)
│   └── **Job RPC:** ``modal_scrape_job_submit``, ``modal_scrape_job_get``, ``modal_scrape_job_list``, ``modal_scrape_job_cancel`` — same Postgres + ``scrape-jobs`` queue as HTTP ``/jobs``, for ``modal.Function.from_name`` callers
│   └── Optional legacy cron in ``backend/src/services/scraper/modal_app.py``
│
└── vecinita-scraper-api (ASGI ``fastapi``) — optional; skipped when ``deploy_modal.sh --no-web``
    └── HTTP: FastAPI under ``/jobs`` (see service OpenAPI)
    └── Auth: e.g. ``REINDEX_TRIGGER_TOKEN`` where applicable
```

**Gateway `/api/v1/integrations/status`:** The API gateway still **HTTP-probes** the **agent** and **database** for operator visibility. **Embedding and model on Modal** are reached via the Modal Python client when configured (not via `*.modal.run` ASGI). **Scraper** may still use HTTP to ``vecinita-scraper-api`` when deployed. Validate with Modal logs or ``modal run`` smoke tests when troubleshooting.

**Gateway Modal job API (`/api/v1/modal-jobs/...`):** When ``MODAL_FUNCTION_INVOCATION`` is enabled, the gateway exposes scrape job **CRUD** that calls the scraper Modal functions above (no direct ``*.modal.run`` to the scraper ASGI). When ``MODAL_SCRAPER_PERSIST_VIA_GATEWAY`` is enabled and ``DATABASE_URL`` is set, **GET** status, **GET** list, and **POST** cancel use Postgres only and do **not** require ``MODAL_FUNCTION_INVOCATION`` (submit still calls Modal to enqueue). After a successful ``POST /api/v1/modal-jobs/scraper``, the gateway spawns the Modal ``trigger_reindex`` function so ``drain_*_queue`` workers run (set ``MODAL_SCRAPER_SUBMIT_AUTO_KICK=0`` to disable if you trigger drains separately). **Tracked reindex spawns** use ``POST /api/v1/modal-jobs/reindex/spawn``; metadata is stored in a Modal **Dict** named by ``MODAL_JOB_REGISTRY_DICT`` (default ``vecinita-gateway-modal-jobs``), with in-memory fallback if the Dict is unavailable. Set ``MODAL_JOB_REGISTRY_DISABLE=1`` to force in-memory only.

**Pipeline persistence without Modal Postgres:** Set ``SCRAPER_GATEWAY_BASE_URL`` (public gateway URL) and the same comma-separated ``SCRAPER_API_KEYS`` on Modal ``vecinita-scraper-env`` as on the Render gateway. Workers send the first key in ``X-Scraper-Pipeline-Ingest-Token``; the gateway accepts any listed segment. Scraper workers then POST pipeline state to ``/api/v1/internal/scraper-pipeline/*`` instead of opening ``psycopg2`` on Modal. See ``docs/deployment/RENDER_SHARED_ENV_CONTRACT.md``.

**See also (feature 012 — queued page ingestion pipeline):** [`specs/012-queued-page-ingestion-pipeline/contracts/render-modal-pipeline-wiring.md`](../../specs/012-queued-page-ingestion-pipeline/contracts/render-modal-pipeline-wiring.md) — Render ↔ Modal topology, env matrix, and **v1 pipeline stage persistence** (structured rows first; DDL only when explicitly migrated).

### Queued page pipeline — timeouts and scale (feature 012)

Summarized from [`specs/012-queued-page-ingestion-pipeline/research.md`](../../specs/012-queued-page-ingestion-pipeline/research.md) **Decision 1–2**:

- **Timeouts:** Modal `@app.function` stubs for scraper/processor/chunk/embed workers use explicit **`timeout=`** (seconds) so a hung crawl or embed step cannot wedge a container indefinitely; tune per environment in `services/scraper/src/vecinita_scraper/workers/*.py` after measuring p95 page time.
- **Invocation:** Prefer **`spawn`** / **`spawn_map`** for drain-driven work where completion is tracked via Postgres/queues rather than blocking the gateway HTTP worker on `.remote()` for long jobs.
- **Observability:** Pass the gateway **correlation id** into Modal job metadata and worker HTTP headers (`X-Request-Id` on pipeline ingest) so **SC-007** join-up works across Render logs and Modal logs (**Decision 2**).

**Frontend (data management) — feature 007:** Point ``VITE_DM_API_BASE_URL`` (or legacy ``VITE_VECINITA_SCRAPER_API_URL``) at the **data-management API** origin; scrape job CRUD uses ``{DM}/jobs``. The gateway ``/api/v1/modal-jobs/scraper`` path remains for **gateway-owned** operator tools, not as the default DM SPA configuration. When legacy scraper ``*.modal.run`` ASGI endpoints still exist for other clients, treat the **DM API deployment** as **authoritative** for DM dashboard scraping.

## Prerequisites

1. **Modal Account**: Create at https://modal.com
2. **Modal CLI**: `pip install modal`
3. **Modal Token**: Generate at https://modal.com/settings/tokens
4. **GitHub Secrets** (for CI/CD): `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`

## Local Development

For local development, use the local embedding service (no Modal required):

```bash
# Terminal 1: Embedding service (FastAPI)
cd backend
python -m uvicorn src.embedding_service.main:app --reload --port 8001

# Terminal 2: API gateway
python -m uvicorn src.api.main:app --reload --port 8004

# Terminal 3: Agent service (if needed)
python -m src.agent.main  # Starts on :8000
```

Set in `.env`:
```env
EMBEDDING_SERVICE_URL=http://localhost:8001
REINDEX_SERVICE_URL=  # Optional for local testing
```

## Manual Modal Deployment

### Step 1: Authenticate with Modal

```bash
# Generate and authenticate with Modal
modal token new

# Verify authentication
modal token info
```

### Step 2: Deploy Services

Canonical **deploy** entry files (add `src/` to `sys.path` so packages resolve) are `services/embedding-modal/main.py`, `services/model-modal/main.py`, `services/scraper/modal_workers_entry.py`, and `services/scraper/modal_api_entry.py`. Modal 1.x: `@modal.asgi_app()` handlers are **nullary**; see the [Modal 1.0 migration guide](https://modal.com/docs/guide/modal-1-0-migration) and [managing deployments](https://modal.com/docs/guide/managing-deployments).

```bash
# Embedding + model + scraper (workers + HTTP API)
./backend/scripts/deploy_modal.sh --all

# Or deploy individually:
./backend/scripts/deploy_modal.sh --embedding
./backend/scripts/deploy_modal.sh --model
./backend/scripts/deploy_modal.sh --scraper

# Optional: legacy monolith cron only (see backend/src/services/scraper/modal_app.py)
# ./backend/scripts/deploy_modal.sh --legacy-scraper-cron
```

**Scraper HTTP API omitted:** pass **`--no-web`** to deploy only ``vecinita-scraper`` workers (skip ``modal_api_entry.py`` / ``vecinita-scraper-api``). Embedding and model Modal apps are always function-only in source; no env flag is required.

**Scraper worker image (Playwright):** The ``vecinita-scraper`` worker image runs ``python -m playwright install --with-deps chromium`` at image build time so Crawl4AI can launch Chromium (pip alone does not ship browser binaries). Expect a longer first build or after Playwright-related dependency bumps; Modal caches image layers afterward.

**If the Modal dashboard still lists ``web_app`` (embedding) or ``api`` (model) as web endpoints:** that is the **previous** deployment. The current repo does not register those handlers on ``vecinita-embedding`` / ``vecinita-model``. Run a fresh ``modal deploy`` for each app from this revision (or let ``modal-deploy.yml`` run on ``main``). Until then, traffic can keep hitting the old ASGI URLs; configure the gateway with ``MODAL_FUNCTION_INVOCATION`` so new traffic uses ``embed_query`` / ``chat_completion`` instead.

After you confirm traffic uses the new apps, use `backend/scripts/modal_teardown_legacy_web.sh` as a checklist for retiring old Modal web routes.

### Step 3: Configure Environment

For **embedding and model on Modal**, configure the gateway with Modal workspace tokens and function invocation (see ``backend/.env.example``: ``MODAL_TOKEN_ID``, ``MODAL_TOKEN_SECRET``, ``MODAL_FUNCTION_INVOCATION=auto`` or ``true``, and optional ``MODAL_EMBEDDING_APP_NAME`` / ``MODAL_MODEL_APP_NAME`` overrides). You can still point ``EMBEDDING_SERVICE_URL`` / ``OLLAMA_BASE_URL`` at a **non-Modal** HTTP service (e.g. local Docker) when not using Modal functions.

For the **recommended function-first mode** on Render, leave ``REINDEX_SERVICE_URL`` empty and enable:

```env
MODAL_FUNCTION_INVOCATION=auto
MODAL_TOKEN_ID=<your-token-id>
MODAL_TOKEN_SECRET=<your-token-secret>
```

Use the **optional scraper HTTP API mode** only when you explicitly want gateway->HTTP forwarding:

```env
REINDEX_SERVICE_URL=https://<your-scraper-api-host>/jobs
REINDEX_TRIGGER_TOKEN=<your-secure-token>  # Set in Modal secret
```

### Step 4: Test Deployments

```bash
# List deployed functions (embedding: embed_query / embed_batch; model: chat_completion / download_*)
modal function list vecinita-embedding
modal function list vecinita-model

# Scraper HTTP API (only if you deployed modal_api_entry.py)
# curl -fsS "https://<vecinita-scraper-api-host>/health"

modal app list --all
```

### Invoking functions (Modal “Apps, Functions, and entrypoints”)

Modal documents two common patterns ([Apps, Functions, and entrypoints](https://modal.com/docs/guide/apps)):

1. **Deployed app** (`modal deploy`) — invoke from **any** Python process that has the Modal SDK and workspace tokens, without importing your service package on the caller:

   ```python
   import modal

   embed = modal.Function.from_name("vecinita-embedding", "embed_query")
   out = embed.remote("hello")  # dict with embedding, model, dimension

   chat = modal.Function.from_name("vecinita-model", "chat_completion")
   out = chat.remote(model="gemma3", messages=[{"role": "user", "content": "Hi"}], temperature=0.0)
   ```

   Optional: `environment_name=...` if you use [Modal environments](https://modal.com/docs/guide/continuous-deployment). The vecinita **gateway** wraps the same idea in `backend/src/services/modal/invoker.py` when `MODAL_FUNCTION_INVOCATION` is enabled. See also [Trigger deployed functions](https://modal.com/docs/guide/trigger-deployed-functions).

2. **Ephemeral app** (`modal run` or `app.run()` in a script) — for local smoke tests or batch jobs: use `with app.run():` and call `.remote()` on the **function object** defined next to your `modal.App` (e.g. a `@app.local_entrypoint()` that calls `embed_query.remote(...)`), as in the Modal guide. Example direct remote entrypoint:

   ```bash
   cd services/embedding-modal
   PYTHONPATH=src modal run main.py::app.embed_query -- "hello"
   ```

   (Adjust `MODAL_PROFILE` / auth if needed; `modal run` CLI syntax follows Modal’s [CLI run](https://modal.com/docs/reference/cli/run) docs.)

## GitHub Actions CI/CD

Continuous deployment follows Modal’s GitHub Actions pattern ([Modal: Continuous deployment](https://modal.com/docs/guide/continuous-deployment)): after the **`Tests`** workflow completes **successfully** on **`main`**, `.github/workflows/modal-deploy.yml` checks out the **same commit** that CI validated and deploys, in order:

1. **Embedding** — `services/embedding-modal/main.py`
2. **Model** — `services/model-modal/main.py`
3. **Scraper** — `services/scraper/modal_workers_entry.py` then `modal_api_entry.py`

You can also run **Actions → Modal Deployment → Run workflow** (`workflow_dispatch`) to deploy the selected services from the branch you choose.

### Setup GitHub Secrets

1. Go to **Settings → Secrets and variables → Actions**
2. Add:
   - `MODAL_TOKEN_ID`: Your Modal token ID
   - `MODAL_TOKEN_SECRET`: Your Modal token secret

Optional repository **Variables** (or secrets): `MODAL_ENVIRONMENT` if you use [multiple Modal environments](https://modal.com/docs/guide/continuous-deployment); `MODAL_API_PROFILE` defaults to `vecinita`.

Manual trigger:
```bash
gh workflow run modal-deploy.yml \
  -f deploy_embedding=true \
  -f deploy_model=true \
  -f deploy_scraper=true
```

## Environment Variables

### Development (Local Services)

```env
EMBEDDING_SERVICE_URL=http://localhost:8001
EMBEDDING_SERVICE_AUTH_TOKEN=  # Optional, empty for local
REINDEX_SERVICE_URL=  # Optional for local testing
```

### Production (Modal Services)

```env
# Modal credentials (for deployment only, not runtime)
MODAL_TOKEN_ID=<your-token-id>
MODAL_TOKEN_SECRET=<your-token-secret>

# Runtime: Modal embedding/model use Function.from_name (set MODAL_FUNCTION_INVOCATION + tokens)
MODAL_FUNCTION_INVOCATION=auto
MODAL_TOKEN_ID=<your-token-id>
MODAL_TOKEN_SECRET=<your-token-secret>
# Optional HTTP-mode scraper fallback only:
# REINDEX_SERVICE_URL=https://<vecinita-scraper-api-host>/jobs
REINDEX_TRIGGER_TOKEN=<your-secret-token>

# Optional: HTTP fallback embedding URL (e.g. local Docker), when not using Modal functions
# EMBEDDING_SERVICE_URL=http://localhost:8001
EMBEDDING_SERVICE_AUTH_TOKEN=${MODAL_TOKEN_SECRET}  # For secured HTTP endpoints when used
```

### Variable Resolution Order

The API gateway resolves embedding delivery with this precedence:

For embedding service:
1. When ``MODAL_FUNCTION_INVOCATION`` is enabled — Modal ``embed_query`` / ``embed_batch`` via the Modal SDK
2. ``EMBEDDING_SERVICE_URL`` (HTTP to another host)
3. ``http://localhost:8001`` (default)

For auth tokens:
1. `EMBEDDING_SERVICE_AUTH_TOKEN` (explicit)
2. `MODAL_TOKEN_SECRET` (Modal routing token)
3. `MODAL_API_KEY` (Modal API key)
4. `MODAL_TOKEN_SECRET` (fallback)

## Troubleshooting

### Modal Authentication Error

```
Error: Not authenticated with Modal. Run: modal token new
```

**Solution**: Generate a new token at https://modal.com/settings/tokens

### Deployment Failed

Check logs with:
```bash
modal app list --all  # List all apps
modal app logs vecinita-embedding  # Stream logs
modal app logs vecinita-scraper
```

### 401 Unauthorized on Embedding Endpoint

**Cause**: Missing or incorrect auth token when `EMBEDDING_SERVICE_AUTH_TOKEN` is configured.

**Solution**: 
```bash
# Get routing secret from Modal app
modal secret get vecinita-secrets

# Or use explicit token
export EMBEDDING_SERVICE_AUTH_TOKEN=<token>
export MODAL_TOKEN_SECRET=<token>
```

### Endpoint Returns 404

**Cause**: App not deployed or wrong URL.

**Solution**:
```bash
# Check deployment status
modal app list --all

# Redeploy if needed
./backend/scripts/deploy_modal.sh --all
```

## Monitoring & Logs

### View Live Logs

```bash
# Embedding service
modal app logs vecinita-embedding --stream

# Scraper service  
modal app logs vecinita-scraper --stream
```

### Check Function Status

```bash
# List all functions in an app
modal function list vecinita-embedding

# Get function details
modal function show vecinita-embedding.embed_query
modal function show vecinita-model.chat_completion
modal function show vecinita-scraper.run_reindex
```

### Scheduled Jobs

The scraper runs on cron schedule (default: `0 2 * * 0` = Sunday 2 AM UTC):

```bash
# View scheduled runs
modal function logs vecinita-scraper.weekly_reindex --stream

# Enqueue work on the scraper API (paths are under ``/jobs`` — see OpenAPI on that host)
curl -fsS -X POST "https://<vecinita-scraper-api-host>/jobs" \
  -H "Authorization: Bearer <REINDEX_TRIGGER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"kind":"example"}'
```

## Security

### Secrets Management

Modal secrets are configured per-app and referenced from each service’s Modal entrypoint (for example `services/scraper/src/vecinita_scraper/api/app.py`).

```python
@modal.asgi_app()
def fastapi():  # scraper API entry; must be nullary on Modal ≥1.0
    # Access secrets via env vars inside Modal function
    token = os.getenv("REINDEX_TRIGGER_TOKEN")
    # ...
```

**To set secrets:**
```bash
# Create modal-secrets
echo "REINDEX_TRIGGER_TOKEN=<your-secure-random-token>" | modal secret create vecinita-secrets

# Update existing secrets
echo "REINDEX_TRIGGER_TOKEN=<new-token>" | modal secret update vecinita-secrets
```

### Token Security

1. Never commit Modal tokens to git
2. Store in `.env.local` (not `.env`)
3. Use GitHub Secrets for CI/CD only
4. Rotate tokens regularly
5. Use `REINDEX_TRIGGER_TOKEN` for public endpoints

## Scaling & Performance

### Embedding Service

Current config:
```python
@modal.function(
    cpu=1.0,
    memory=2048,
    timeout=3600,
)
```

To scale:
- Increase `cpu` for faster embeddings
- Increase `memory` for larger models
- Tune Modal autoscaler settings (`max_containers`, `scaledown_window`, etc.; see [Modal 1.0 migration](https://modal.com/docs/guide/modal-1-0-migration))

### Scraper Service

Current config:
```python
@modal.function(
    cpu=2.0,
    memory=4096,
    timeout=3 * 60 * 60,
)
```

For larger scrapes:
- Increase `memory` for parallel scraping
- Adjust `REINDEX_CRON_SCHEDULE` for frequency
- Set `SCRAPER_REINDEX_CLEAN=true` for full re-index

## Advanced Configuration

### Custom Embedding Models

```bash
# Update model in .env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_PROVIDER=sentence-transformers  # or 'fastembed'

# Redeploy
./backend/scripts/deploy_modal.sh --embedding
```

### Custom Cron Schedule

```bash
# 2 AM UTC, every Sunday
REINDEX_CRON_SCHEDULE=0 2 * * 0

# 6 AM UTC, every day
REINDEX_CRON_SCHEDULE=0 6 * * *

# Disable scheduled runs (manual only)
REINDEX_CRON_SCHEDULE=  # Empty to disable
```

### Multi-Region Deployment

Modal supports regional deployment; configure on `@app.function(...)` / image build in the relevant service `src/vecinita/app.py` (consult current Modal docs for supported `region` parameters).

## Related Documentation

- [Modal Documentation](https://modal.com/docs)
- [Vecinita Architecture](./docs/architecture/)
- [API Gateway Documentation](./backend/src/api/README.md)
- [Embedding Service API](./backend/src/embedding_service/README.md)
