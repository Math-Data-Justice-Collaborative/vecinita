# Deployment Integration Plan

> **Project**: Vecinita  
> **Last updated**: 2026-05-24 (EV-001 connectivity delta)

## Overview

Hybrid deployment: **DigitalOcean** (US `nyc1` or `sfo3`) for ChatRAG Backend, internal write API, both frontends, and **Managed Postgres**; **Modal** (US workspace) for Data Management ASGI, ingest workers, FastEmbed, and **vLLM** (primary LLM per RD-021). Modal workers **do not** hold `DATABASE_URL`; they call the DO internal write API.

## Services

| Deploy unit | Platform | Notes |
|-------------|----------|-------|
| chat-rag-backend | DO App Platform | FastAPI, LlamaIndex, pgvector read |
| chat-rag-frontend | DO App Platform (static) | Vite build |
| data-management-frontend | DO App Platform (static) | Admin UI |
| DO internal write API | DO App Platform (**standalone** app) | Sole holder of `DATABASE_URL` for writes from Modal; audited S8.4 |
| data-management-modal | Modal | ASGI + queues + scrape |
| vecinita-embedding | Modal | FastEmbed 384-dim |
| vecinita-llm | Modal | **vLLM** — **Qwen2.5-1.5B-Instruct** on **T4** (scale-to-zero) |
| database | DO Managed Postgres | Smallest viable tier |

**Topology note (RD-022):** User selected **multi-app** on DO (separate deployables per backend). **05-verify-tech / TP-009:** pilot **~$42–48/mo** fits ≤ **$50** cap with scale-to-zero GPU; consolidate DO if overrun.

## Database

- **Engine:** PostgreSQL 15+ with `pgvector` extension
- **Dimension:** `vector(384)` for FastEmbed
- **Migrations:** Alembic from `apps/database`
- **Connection:** `DATABASE_URL` only on DO services
- **Pool sizing:** SQLAlchemy pool `pool_size=5`, `max_overflow=5` on DO basic tier (04-tech-plan)

## Secrets & environment

| Secret | Where stored |
|--------|----------------|
| `DATABASE_URL` | DO app secrets (backends only) |
| `VECINITA_MODAL_TOKEN_*` | DO ChatRAG secrets |
| `VECINITA_INTERNAL_API_KEY` | DO + Modal (matching) |
| Modal tokens | Modal dashboard; not in browser |

Frontends receive **public** API base URLs only at build time (`VITE_*`).

### EV-001 — Browser connectivity (F19–F22)

| Variable | App | Purpose |
|----------|-----|---------|
| `VITE_VECINITA_CHAT_API_URL` | chat-rag-frontend | Ask + **public browse** (`GET /api/v1/documents`, `/tags`) |
| `VECINITA_CORS_ORIGINS` | chat-rag-backend | Must include chat frontend origin for new **GET** routes (H4) |
| `VITE_VECINITA_CORPUS_API_URL` | data-management-frontend | Admin chunk/tag PATCH routes |
| `VITE_VECINITA_CORPUS_API_KEY` | data-management-frontend | Bearer for internal-write (build-time; review in 04-tech-plan) |

**Redeploy order (EV-001):** Deploy chat-rag-backend with CORS + new routes **before** chat-rag-frontend browse UI sign-off (H4–H5).

## Entrypoints & triggers

| Component | Entry | Trigger |
|-----------|-------|---------|
| ChatRAG API | `uvicorn` on DO | HTTP |
| Internal write API | `uvicorn` on DO | HTTP from Modal |
| Data mgmt ASGI | Modal `@asgi_app` | HTTP (proxy auth) |
| Ingest worker | Modal `@function` queue | Job enqueue |
| Migrations | `alembic upgrade head` | Deploy hook / manual |
| Local dev | `docker-compose`, `modal serve` | Developer |

## Pipeline mapping

| Component | Implementation | Deploy unit |
|-----------|----------------|-------------|
| Query | `packages/rag` + ChatRAG Backend | chat-rag-backend |
| Ingest | `packages/ingest` + Modal workers | data-management-modal |
| Embed | FastEmbed service | vecinita-embedding |
| Generate | vLLM | vecinita-llm |
| Persist | Internal write API | DO app |
| Schema | `apps/database` | migrations job |

## Scaling & performance

- ChatRAG p95 target: **< 15s** (spec)
- Modal: scale-to-zero on ASGI where supported; GPU for vLLM sized in 04-tech-plan
- No horizontal multi-region in v1

## Migration checklist

- [ ] Enable pgvector on DO Postgres
- [ ] Run Alembic revisions
- [ ] Load seed corpus (staging; production may include committed fixtures per data-management-plan)
- [ ] Smoke: `/health`, UJ-001 sample ask
- [ ] Privacy tests in CI green

## Cost estimation

See **`docs/execution-plan.md` §Cost Estimate** for line items (2026-05-19).

| Resource | Est. $/mo (pilot) | Notes |
|----------|-------------------|-------|
| DO Managed Postgres (1 GB) | ~15 | Basic tier |
| DO multi-app (4+ services) | ~20–27 | chat-rag-backend, internal-write-api, 2× static |
| Modal GPU T4 (vLLM) | ~5–20 | Scale-to-zero; not 24×7 |
| Modal CPU embed/scrape | ~2–8 | Per invoke |

**Targets:** ≤ **$25/mo** preferred, ≤ **$50/mo** hard cap (ADR-004).  
**04-tech-plan gate:** Pilot traffic **~$42–48/mo** achievable; consolidate DO first if over cap (user decision).

## Open questions

- Budget alerts at 80%/100% of $50 — implement in T14.4 / 13-deploy-smoke
