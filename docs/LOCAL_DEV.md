# Local development (F18, UJ-004)

Run Vecinita on your machine with Docker Postgres, uv Python workspace, and optional Modal `serve` for GPU/CPU workers.

## Prerequisites

- Docker (for Postgres + pgvector)
- [uv](https://docs.astral.sh/uv/) (Python 3.11 workspace)
- Node.js 20+ (frontends)
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
uv run uvicorn vecinita_chat_rag_backend.app:create_app --factory --host 0.0.0.0 --port 8000
```

For API-only work without Modal, use `pytest` — integration tests mock embed/LLM HTTP.

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

## Configuration

| Source | Purpose |
|--------|---------|
| `infra/vecinita.yaml` | Non-secret local defaults (URLs, `top_k`, chunk size) |
| `.env` / shell exports | Secrets and overrides (`DATABASE_URL`, API keys) |
| `docs/config-spec.md` | Full `VECINITA_*` / `VITE_*` reference |

Precedence: env vars > `vecinita.yaml` > documented defaults.
