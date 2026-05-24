# Configuration Specification

> **Project**: Vecinita  
> **Last updated**: 2026-05-24 (EV-001)

## Precedence

CLI flags (where present) > Environment variables > Config file > Defaults

## Environment Variables

### Shared

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DATABASE_URL` | string | — | Yes (DO backends only) | Postgres connection; **not** on Modal workers |
| `VECINITA_ENV` | string | `development` | No | `development` \| `staging` \| `production` |
| `VECINITA_LOG_LEVEL` | string | `INFO` | No | Logging level |
| `VECINITA_LOG_RETENTION_DAYS` | int | `7` | No | Max retention; no raw prompts in persistent logs |

### ChatRAG Backend (DO)

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_TOP_K` | int | `5` | No | Retrieval chunk count |
| `VECINITA_MIN_RETRIEVAL_SCORE` | float | `0.2` | No | Minimum pgvector similarity (`1 - distance`); chunks below are dropped |
| `VECINITA_CHAT_MAX_TOKENS` | int | `256` | No | Max tokens sent to Modal LLM per chat answer |
| `VECINITA_MODAL_EMBED_URL` | string | — | Yes (prod) | Modal FastEmbed base URL |
| `VECINITA_MODAL_LLM_URL` | string | — | Yes (prod) | Modal LLM base URL |
| `VECINITA_MODAL_TOKEN_ID` | string | — | Yes (DO→Modal) | Modal credential (DO secret) |
| `VECINITA_MODAL_TOKEN_SECRET` | string | — | Yes | Modal credential |
| `VECINITA_LLM_BACKEND` | string | `vllm` | No | `vllm` primary; `ollama` fallback only per ADR-009 |
| `VECINITA_REQUEST_TIMEOUT_S` | int | `120` | No | Upstream Modal timeout (cold-start margin; see R5) |
| `VECINITA_BROWSE_PAGE_SIZE` | int | `20` | No | Default page size for `GET /api/v1/documents` |
| `VECINITA_MAX_TAGS_PER_DOCUMENT` | int | `10` | No | Hard cap on document tags |
| `VECINITA_MAX_TAGS_PER_CHUNK` | int | `5` | No | Hard cap on chunk tags |
| `VECINITA_TAG_SEED_PATH` | string | `data/fixtures/tags/seed_tags.json` | No | Starter tag vocabulary for LLM + browse facets |

### DO internal write API

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_INTERNAL_API_KEY` | string | — | Yes | Shared secret Modal workers use |
| `DATABASE_URL` | string | — | Yes | Postgres |

### Data Management (Modal)

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_DO_WRITE_API_URL` | string | — | Yes | DO internal write API base URL |
| `VECINITA_INTERNAL_API_KEY` | string | — | Yes | Matches DO secret |
| `VECINITA_CHUNK_SIZE_TOKENS` | int | `256` | No | Ingest chunk target (tokenizer-based) |
| `VECINITA_SCRAPE_TIMEOUT_S` | int | `30` | No | Per-URL fetch timeout |
| `VECINITA_LLM_TAG_MAX_TOKENS` | int | `128` | No | Max tokens for LLM tagging completion per document |

### Frontends

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VITE_VECINITA_CHAT_API_URL` | string | `http://localhost:8000` | Yes (build) | ChatRAG Backend base |
| `VITE_VECINITA_ADMIN_API_URL` | string | — | Yes | Modal ASGI or gateway URL for jobs |
| `VITE_VECINITA_CORPUS_API_URL` | string | — | Yes (admin) | Internal write API base for corpus/tag admin |
| `VITE_VECINITA_CORPUS_API_KEY` | string | — | Yes (admin build) | Bearer token for tag/chunk admin routes |

## Recommended defaults (spec)

| Parameter | Value | Reference |
|-----------|-------|-----------|
| `VECINITA_TOP_K` | 5 | RD interview |
| `VECINITA_CHUNK_SIZE_TOKENS` | 256 | RD interview |
| Embedding dimension | 384 | FastEmbed / pgvector |
| `VECINITA_LLM_BACKEND` | `vllm` | ADR-009, RD-021 |

## Validation rules

| Rule | Enforcement |
|------|-------------|
| `VECINITA_TOP_K` ≥ 1 and ≤ 50 | Config module at startup |
| `VECINITA_MIN_RETRIEVAL_SCORE` ≥ 0 and < 1 | Config module at startup |
| `VECINITA_CHAT_MAX_TOKENS` ≥ 32 and ≤ 2048 | Config module at startup |
| `VECINITA_CHUNK_SIZE_TOKENS` ≥ 64 | Ingest validation |
| `VECINITA_MAX_TAGS_PER_DOCUMENT` ≥ 1 and ≤ 20 | Config module |
| `VECINITA_MAX_TAGS_PER_CHUNK` ≥ 1 and ≤ 10 | Config module |
| `VECINITA_BROWSE_PAGE_SIZE` ≥ 1 and ≤ 100 | Config module |
| Reject unknown `VECINITA_*` in strict mode | Optional dev strictness |
| No identity fields in public API bodies | OpenAPI + Pydantic models |

## Configuration files

**`vecinita.yaml`** (v1, audited S5.5): Optional repo-root or `infra/vecinita.yaml` for local/staging defaults. Production on DO/Modal still uses platform secrets for sensitive values; YAML holds non-secret defaults (e.g. `top_k`, `chunk_size_tokens`, service URLs for local compose).

```yaml
# Example (non-secret defaults only)
env: development
chat_rag:
  top_k: 5
  request_timeout_s: 60
ingest:
  chunk_size_tokens: 256
  scrape_timeout_s: 30
```

Precedence: CLI flags > environment variables > `vecinita.yaml` > table defaults above.

## CLI flags

⚠️ **Not discussed:** No user-facing CLI in v1 beyond developer scripts (`alembic`, `modal`, `docker-compose`).
