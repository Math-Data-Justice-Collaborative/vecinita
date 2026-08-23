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
export VECINITA_MODAL_LLM_URL=http://localhost:8004     # after modal serve llm (prod ChatRAG)

# Staging/prod (vecinita Modal workspace — see infra/modal/.env.example):
# export VECINITA_MODAL_EMBED_URL=https://vecinita--vecinita-embedding-embedding-api.modal.run
# export VECINITA_MODAL_LLM_URL=https://vecinita--vecinita-llm-fastapi-app.modal.run
uv run uvicorn vecinita_chat_rag_backend.app:create_app --factory --host 0.0.0.0 --port 8000
```

**Playground LLM** (admin / eval sandbox only — never ChatRAG):

```bash
# After: modal serve infra/modal/llm_playground_app.py
export VECINITA_MODAL_LLM_PLAYGROUND_URL=http://localhost:8005
```

ChatRAG must use `VECINITA_MODAL_LLM_URL` (prod `vecinita-llm`), not the playground URL.

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

See [infra/modal/README.md](../infra/modal/README.md) for `modal serve` commands per app
(embedding, data-management, `vecinita-llm`, `vecinita-llm-playground`). LoRA fine-tune
(`vecinita-llm-finetune`) is implemented (`infra/modal/finetune_app.py`); pins in
`infra/modal/finetune_pins.py`.

### Corpus automations / freshness / FT (local knobs)

Defaults are off. Full reference: [config-spec.md](config-spec.md).

| Env | Default | Role |
|-----|---------|------|
| `VECINITA_AUTOMATIONS_KILL_SWITCH` | `false` | Hard stop — no new catch-up or FT train enqueue when `true` |
| `VECINITA_AUTOMATIONS_ENABLED` | `false` | Catch-up enqueue enable |
| `VECINITA_FRESHNESS_ENABLED` | `false` | Scheduled freshness refresh |
| `VECINITA_FRESHNESS_STALE_DAYS` | `30` | Stale threshold |
| `VECINITA_FINETUNE_ENABLED` | `false` | Fine-tune feature flag |
| `VECINITA_FINETUNE_ADAPTER_ID` | empty | Promoted LoRA pin on prod LLM (empty = base) |
| `VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID` | empty | Optional pre-promote candidate on playground only |

Do **not** enable automations or promote adapters against live prod without an explicit
AskQuestion approval. Admin Automations / freshness UI journeys: see `docs/user-journeys.md`
(UJ-080+).

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
| Agent stop | After agent turn | `make check-fast` + `make test-fast` (lint **+ typecheck** + units) |
| **git commit** (Husky pre-commit) | Every commit | `make typecheck` + `make security-scan` + job_type dispatch |
| **git push** (Husky pre-push) | Everyday push | `make lint` + `make test-fast` only |
| Medium (opt-in push) | `VECINITA_MEDIUM_PRE_PUSH=1` | `make check` + `make test-fast` |
| Full | **Before opening a PR** | `make ci-push` (alias: `make ci-pr-ready`) |

```bash
make lint          # ruff + ESLint (pre-push default)
make check-fast    # lint + typecheck (no format-check; agent stop)
make test-fast     # unit tests for locally changed apps/packages only
make ci-push       # full CI parity — run before marking a PR ready
make ci-pr-ready   # alias for ci-push
```

Husky installs on `npm ci` (`prepare` script). **Pre-push is lean** (lint + units);
heavier local gates run on **pre-commit**. GitHub CI remains the merge gate for
**unit** tests, format-check, audit, **unit coverage** (with PR comment), and production
builds. **Compose-backed** suites (`integration` / `e2e` / `privacy` / `smoke` / `eval` /
`bugs`) run locally via `make test-py` / `make ci-push` (S027-D34 / F62).

```bash
# Skip pre-commit (emergencies only):
VECINITA_SKIP_PRE_COMMIT=1 git commit

# Opt-in medium tier on push (adds format-check):
VECINITA_MEDIUM_PRE_PUSH=1 git push

# Opt-in full local parity on every push:
VECINITA_FULL_PRE_PUSH=1 git push

# Skip pre-push entirely (emergencies only):
VECINITA_SKIP_PRE_PUSH=1 git push
```

## Unit coverage gate (F31 / ADR-019)

Per-component **≥95% line and branch** coverage on all **fifteen** components
(6 `apps/*` + 9 `packages/*`). Enforced locally and in CI via
`scripts/test/print_unit_coverage_summary.py --enforce`.

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

## Commits and PRs

Developer-facing git text uses short plain English. Tracking IDs (features, ADRs, tasks)
are optional citations after the English — not the subject by themselves.

Examples:

```text
feat: enqueue catch-up for failed embeds (F75)
fix: restore admin pagination (#112)
```

PR titles: `Corpus automations catch-up (F75)` — not `[M127] …`.

Details: `.cursor/rules/atomic-commits.mdc`, `.cursor/rules/developer-facing-language.mdc`.
