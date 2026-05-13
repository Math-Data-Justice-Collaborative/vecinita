# Contributing

## Repository Layout

```
apps/
  frontend/              # React/Vite UI (git submodule)
  backend/               # Legacy path — no longer contains service submodules (see apps/backend/README.md)
packages/
  shared-schemas/        # Pydantic API types
  service-clients/       # Typed HTTP clients
  shared-config/         # Configuration
  shared-logging/        # Logging
infra/                   # Docker and Kubernetes
scripts/                 # Dev utilities
docs/                    # Documentation
```

## Local Development

### Prerequisites

- Python >= 3.11
- Node.js >= 18
- Docker and Docker Compose
- [modal](https://modal.com/docs/guide) CLI (for Modal-backed scraper/embedding deploys)

### First-time setup

After cloning, initialise the **frontend** submodule:

```bash
git submodule update --init apps/frontend
```

### Start Everything (model + frontend)

```bash
docker compose -f infra/docker-compose.yml up --build
```

### Run a Single Backend Service

No proxy service is required. Frontend calls scraper/model/embedding directly
through `VITE_*` endpoint environment variables.

**Model service** (local Ollama via compose): built from `infra/docker/model-service.Dockerfile`
(clones [vecinita-model](https://github.com/Math-Data-Justice-Collaborative/vecinita-model)).

**Scraper service** (Modal serverless): work in [vecinita-scraper](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper)
or monorepo `modal-apps/scraper`.

```bash
git clone https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper.git
cd vecinita-scraper
cp .env.example .env
modal serve   # hot-reloads locally via Modal sandbox
```

**Embedding service** (Modal serverless): work in the vecinita-embedding repository or monorepo `modal-apps/embedding-modal`.

```bash
modal serve main.py
```

### Run the Frontend

```bash
cd apps/frontend
npm install
npm run dev   # Vite dev server on http://localhost:5173
```

## Code Standards

### Python

- Format: [ruff](https://github.com/astral-sh/ruff)
- Line length: 100
- Python >= 3.11 syntax (use `str | None` instead of `Optional[str]`)

### TypeScript / JavaScript

- Format: Prettier (configured per service)
- Lint: ESLint

## Adding a New Shared Schema

1. Add your Pydantic model to `packages/shared-schemas/shared_schemas/`
2. Export it from `shared_schemas/__init__.py`
3. Reinstall: `pip install -e packages/shared-schemas`

## Adding a New Service Client

1. Add your async client to `packages/service-clients/service_clients/`
2. Export it from `service_clients/__init__.py`
3. Add a test in `packages/service-clients/tests/`

## Pull Requests

- Open against `main`
- Include tests for any logic changes
- Do not import from another `apps/` service's internals
