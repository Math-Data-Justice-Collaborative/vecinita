# Local development (F18, UJ-004)

Run Vecinita on your machine with Docker Postgres, uv Python workspace, and optional Modal `serve` for GPU/CPU workers.

## Prerequisites

- Docker (for Postgres + pgvector)
- [uv](https://docs.astral.sh/uv/) (Python 3.11 workspace)
- Node.js 24+ (frontends) — see `.nvmrc` (`nvm use` or [fnm](https://github.com/Schniz/fnm): `fnm install && fnm use`). **`make lint-fe` / `make test-fe`** auto-activate Node 24 via `scripts/ensure_node24.sh` when fnm is installed.
- [Modal CLI](https://modal.com/docs/guide) (optional — only for live embed/LLM/data-mgmt; tests mock HTTP)

## 1. Postgres

```bash
docker compose -f infra/docker-compose.yml up -d postgres
```

Wait until healthy: `docker compose -f infra/docker-compose.yml ps`

Default connection (matches `infra/vecinita.yaml`):

```text
postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
```

Export for shells:

```bash
export DATABASE_URL=postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
```

## 2. Migrations and seed corpus

```bash
cd apps/database
uv run alembic upgrade head
uv run python -c "from vecinita_database.seeds.load import load_corpus; load_corpus()"
cd ../..
```

## 3. Python backends (DO services locally)

From repo root:

```bash
uv sync
```

**Internal write API** (port 8002):

```bash
export DATABASE_URL=postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
export VECINITA_INTERNAL_API_KEY=dev-internal-key
uv run uvicorn vecinita_internal_write_api.app:create_app --factory --host 0.0.0.0 --port 8002
```

**ChatRAG backend** (port 8000) — point at Modal URLs or local mocks:

```bash
export DATABASE_URL=postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
export VECINITA_MODAL_EMBED_URL=http://localhost:8003   # after modal serve embedding
export VECINITA_MODAL_LLM_URL=http://localhost:8004     # after modal serve llm

# Staging/prod (vecinita Modal workspace — see infra/modal/.env.example):
# export VECINITA_MODAL_EMBED_URL=https://vecinita--vecinita-embedding-embedding-api.modal.run
# export VECINITA_MODAL_LLM_URL=https://vecinita--vecinita-llm-fastapi-app.modal.run
uv run uvicorn vecinita_chat_rag_backend.app:create_app --factory --host 0.0.0.0 --port 8000
```

For API-only work without Modal, use **`uv run pytest`** (or `bash scripts/run_tests.sh`) — integration tests mock embed/LLM HTTP. Bare `pytest` will not resolve workspace packages.

## 4. Frontends

**ChatRAG** (port 5173):

```bash
cd apps/chat-rag-frontend
cp .env.example .env
npm install && npm run dev
```

**Data management** (port 5174):

```bash
cd apps/data-management-frontend
cp .env.example .env
npm install && npm run dev
```

## 5. Modal `serve` (optional)

See [infra/modal/README.md](../infra/modal/README.md) for `modal serve` commands per app.

## 6. Smoke checks

```bash
curl -s http://localhost:8000/health | jq .
curl -s -X POST http://localhost:8000/api/v1/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What are the food pantry hours?"}' | jq .
```

Automated UJ-004: `uv run pytest tests/e2e/test_uj004_local_bootstrap.py -q`

## Playwright UI E2E (T0-ui)

Browser smoke tests against production bundles (`vite preview`) with mocked APIs. See `tests/ui/README.md`.

```bash
make test-ui
# or: bash scripts/ui/run_playwright.sh
```

Requires Node 24 and a one-time Chromium install (`npx playwright install chromium`, included in `run_playwright.sh`).

## Fast checks vs full CI

| Tier | When | Command |
|------|------|---------|
| Fast | Agent stop hook; **git push** (Husky) | `make check-fast` + `make test-fast` |
| Medium | Before commit (optional) | `make check` + `make test-fast` |
| Full | **Before opening a PR** | `make ci-push` (alias: `make ci-pr-ready`) |

```bash
make check-fast    # lint + typecheck (no format-check)
make test-fast     # unit tests for locally changed apps/packages only
make test-coverage-fe FE_APP=data-management-frontend  # one frontend coverage loop
make ci-push       # full CI parity — run before marking a PR ready
make ci-pr-ready   # alias for ci-push
```

Husky installs on `npm ci` (`prepare` script). Pre-push runs **fast tier** only; GitHub
CI is the merge gate for format-check, audit, full tests, coverage, and production builds.

```bash
# Opt-in medium tier on push (adds format-check):
VECINITA_MEDIUM_PRE_PUSH=1 git push

# Opt-in full local parity on every push:
VECINITA_FULL_PRE_PUSH=1 git push

# Skip pre-push entirely (emergencies only):
VECINITA_SKIP_PRE_PUSH=1 git push
```

## Unit coverage gate (F31 / ADR-019)

Per-component **≥95% line and branch** coverage on all twelve `packages/*` and `apps/*` components. Enforced locally and in CI via `scripts/test/print_unit_coverage_summary.py --enforce`.

**Run (same as CI `coverage` job):**

```bash
make test-unit-coverage
```

This runs Python `tests/unit` with pytest-cov, both frontends with Vitest coverage, then prints a per-component summary. Exit code **1** if any component is below 95% line or branch.

**Gate unit tests only (no full suite):**

```bash
uv run pytest tests/unit/test_coverage_gate.py -q
```

**HTML reports:** `htmlcov/` (Python), `coverage/chat-rag-frontend/`, `coverage/data-management-frontend/`.

See `docs/adr/ADR-019-per-component-coverage-95.md` and `docs/test-plan.md` §F31.

## Configuration

| Source | Purpose |
|--------|---------|
| `infra/vecinita.yaml` | Non-secret local defaults (URLs, `top_k`, chunk size) |
| `.env` / shell exports | Secrets and overrides (`DATABASE_URL`, API keys) |
| `docs/config-spec.md` | Full `VECINITA_*` / `VITE_*` reference |

Precedence: env vars > `vecinita.yaml` > documented defaults.
