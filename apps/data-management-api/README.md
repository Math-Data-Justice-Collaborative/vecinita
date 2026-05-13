# vecinita-data-management

Monorepo for the Vecinita data management platform — a community-driven data collection and analysis system.

When checked out inside the **vecinita** umbrella repo, this tree lives at
`apis/data-management-api/` (clone from [github.com/Math-Data-Justice-Collaborative/vecinita](https://github.com/Math-Data-Justice-Collaborative/vecinita)).

**Remote-only backends (feature `003-consolidate-scraper-dm`)**: configure HTTP origins via
`SCRAPER_SERVICE_BASE_URL`, `EMBEDDING_SERVICE_BASE_URL`, and `MODEL_SERVICE_BASE_URL` (see
`packages/shared-config` `BaseServiceSettings`, which also accepts legacy `VECINITA_*_API_URL`
names). Prefer `packages/service-clients` (`ScraperClient`, `EmbeddingClient`, `ModelClient`) for
service calls — the old `apps/backend/{scraper,embedding,model}-service` git submodules are removed.

## Repository Structure

```
repo/
  apps/
    frontend/              # React/Vite UI  (submodule: vecinita-data-management-frontend)
    backend/               # FastAPI data-management API (see apps/backend/README.md)

  packages/
    shared-schemas/        # Pydantic/Zod shared types and API contracts
    service-clients/       # Typed HTTP clients for inter-service calls
    shared-config/         # Shared configuration utilities
    shared-logging/        # Shared logging utilities

  infra/
    docker-compose.yml     # Local development orchestration (model + frontend)
    docker/                # Dockerfiles (including upstream clones for compose)
    k8s/                   # Kubernetes manifests

  scripts/                 # Developer utility scripts
  docs/                    # Architecture and developer documentation
```

Deployable scraper / embedding / model **source trees** live in separate repositories (and in the
vecinita monorepo as `modal-apps/scraper`, `modal-apps/embedding-modal`, `modal-apps/model-modal`).

## Dependency Model

```
frontend  →  scraper / model / embedding  (HTTP, via VITE_* or remote URLs)
```

Rules enforced by convention:

- `apps` can depend on `packages`; `packages` must **not** depend on `apps`
- No circular dependencies
- Cross-service communication happens over HTTP, **not** by importing another deployable’s Python package
- Shared code (schemas, clients, utilities) lives in `packages/`

## Services

| Capability | Where to run / build | Notes |
|------------|------------------------|-------|
| frontend | `apps/frontend` (submodule) | Vite UI |
| scraper | [vecinita-scraper](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper) · monorepo `modal-apps/scraper` | Modal + Docker |
| model | [vecinita-model](https://github.com/Math-Data-Justice-Collaborative/vecinita-model) · monorepo `modal-apps/model-modal` | Modal + local compose |
| embedding | [vecinita-embedding](https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding) · monorepo `modal-apps/embedding-modal` | Modal |

## Shared Packages

| Package | Path | Description |
|---------|------|-------------|
| shared-schemas | `packages/shared-schemas` | API request/response types (Pydantic + Zod) |
| service-clients | `packages/service-clients` | Typed Python clients for service-to-service calls |
| shared-config | `packages/shared-config` | Shared configuration loading utilities |
| shared-logging | `packages/shared-logging` | Structured logging setup |

## Quick Start

### Clone with submodules

Only the **frontend** remains a nested submodule:

```bash
git clone https://github.com/Math-Data-Justice-Collaborative/vecinita-data-management.git
cd vecinita-data-management
git submodule update --init apps/frontend
```

From the **vecinita** monorepo root, initialise this repo with:

```bash
git submodule update --init apis/data-management-api
```

### Local Development (Docker Compose)

Set remote scraper/embedding URLs in `.env` (or rely on compose defaults pointing at Modal), then:

```bash
docker compose -f infra/docker-compose.yml up --build
```

This starts:

- Frontend: http://localhost:3000
- Model service: http://localhost:8003 (Ollama-backed image built from `infra/docker/model-service.Dockerfile`)

### Deploying Modal Services

Use the upstream repositories (same code as vecinita monorepo `services/*`):

```bash
git clone https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper.git
cd vecinita-scraper
pip install modal
modal deploy
```

Repeat for embedding/model from their repos as needed.

### Deploying the API on Render

- **vecinita monorepo**: production image for `vecinita-data-management-api-v1` is built from
  `modal-apps/scraper` (see root `render.yaml` — avoids nested submodule checkouts).
- **Standalone clone of this repo**: the root `Dockerfile` clones [vecinita-scraper](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper) at build time so the image does not depend on `apps/backend/scraper-service`.

Recommended settings when building this repository directly:

- Runtime: Docker
- Dockerfile Path: `Dockerfile`
- Health Check Path: `/health`

## CORS (browser ↔ DM API)

The FastAPI surface must allow browser calls from the **data-management** Vite app. Set **`ALLOWED_ORIGINS`** (comma-separated) to include every origin that loads the SPA:

| Origin | Typical use |
|--------|-------------|
| `http://localhost:5174` | DM Vite dev server (default in the vecinita monorepo) |
| `http://localhost:4173` | DM preview / Playwright `webServer` |
| `http://localhost:5173` | Chat SPA when testing both apps against the same API |

Mirror the same values in the umbrella repo root **`.env.local.example`** (`ALLOWED_ORIGINS=...`) so local Compose and Render templates stay aligned.

## Pact (Modal RPC via ``service_clients``)

From the vecinita repo root, with the usual ``PYTHONPATH`` for this subtree (see root **Makefile** ``test-backend-unit``), generate the sync-message pact:

`pytest apis/data-management-api/packages/service-clients/tests/pact/test_dm_service_clients_modal_message_pact.py -q`

Output: ``apis/data-management-api/pacts/vecinita-dm-service-clients-vecinita-modal-sdk.json`` (gitignored). Provider replay is documented in the umbrella ``backend/tests/pact/README.md``.

**Jobs proxy → scraper** (browser ``/jobs`` forwarding):

``pytest apis/data-management-api/tests/pact/dm_api_jobs_proxy_scraper_consumer_pact.py -q`` (same ``PYTHONPATH`` as in the root **Makefile** ``test-backend-unit`` scraper line) → ``apis/data-management-api/pacts/vecinita-dm-api-vecinita-scraper-jobs-http.json``.

## Contributing

See [docs/contributing.md](docs/contributing.md) for development guidelines, branching strategy, and PR process.

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.
