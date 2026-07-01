# Deployment Integration Plan

> **Project**: Vecinita  
> **Last updated**: 2026-06-30 (EV-007 F35 ext — invite redirect chain)

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

### EV-002 — Admin dashboard, bulk ops, stats, audit (F23–F29)

| Variable | App | Purpose |
|----------|-----|---------|
| `VECINITA_CHAT_RAG_URL` | internal-write-api | Health aggregator polls ChatRAG `/health` |
| `VECINITA_MODAL_EMBED_URL` / `LLM_URL` / `DATA_MGMT_URL` | internal-write-api | Health aggregator polls Modal services |
| `VECINITA_CHAT_FRONTEND_URL` / `ADMIN_FRONTEND_URL` | internal-write-api | Health aggregator HTTP check on static sites |
| `VECINITA_HEALTH_TIMEOUT_MS` | internal-write-api | Per-service timeout (default 5000 ms) |
| `VECINITA_INTERNAL_WRITE_URL` + `VECINITA_INTERNAL_API_KEY` | chat-rag-backend | Fire-and-forget `POST /internal/v1/stats/served` after ask |
| `VECINITA_STATS_ENABLED` | chat-rag-backend | Disable stats POST when `false` |
| `VECINITA_AUDIT_RETENTION_DAYS` | internal-write-api | `POST /internal/v1/audit/cleanup` retention (default 365; `0` = skip) |

New write API routes (admin UI via `VITE_VECINITA_CORPUS_API_URL` + Bearer):

- `GET /internal/v1/stats/summary`, `GET /internal/v1/stats/top-served`, `POST /internal/v1/stats/served`
- `GET /internal/v1/health/all`
- `DELETE/PATCH/POST` `/internal/v1/documents/bulk*`
- `GET /internal/v1/audit`, `GET /internal/v1/documents/{id}/history`, `POST /internal/v1/audit/cleanup`

**Alembic:** revision `20260526_0003` (`audit_log`, `document_versions`, `document_serving_stats`).

**Redeploy order (EV-002, TP-029):**

1. `alembic upgrade head` on staging/prod Postgres
2. `internal-write-api` (new endpoints + health env vars)
3. `chat-rag-backend` (stats POST integration)
4. `data-management-frontend` (admin UI overhaul)

Modal apps **do not** require redeploy for EV-002 (health aggregator on DO write API per ADR-017).

### EV-004 — Shared frontend i18n/UI + admin bilingual (F31)

**Scope:** Client-only locale; no new backend env vars, secrets, or CORS changes.

| Artifact | Platform | Notes |
|----------|----------|-------|
| `packages/frontend-i18n` | npm workspace | Pure TS; linked via workspace source imports in CI |
| `packages/frontend-ui` | npm workspace | React + Tailwind + minimal shadcn; bundled via Vite from source |
| chat-rag-frontend | DO static | Tailwind migration + shared package imports |
| data-management-frontend | DO static | LocaleProvider + ~120+ translated strings |

**Monorepo wiring:** Root `package.json` npm workspaces for `apps/*` and `packages/frontend-*` (R38). CI frontend matrix installs from root or builds packages before app `npm ci`.

**Browser locale:** `localStorage` key `vecinita.locale` — shared across both DO static origins when operator uses same browser profile; no cross-origin cookie.

**Redeploy order (EV-004):**

1. CI links shared packages via npm workspaces (source imports — no separate `dist/` build per TP-031)
2. Deploy **chat-rag-frontend** and **data-management-frontend** in the same release window (TP-038)

No redeploy required: chat-rag-backend, internal-write-api, Modal apps, Postgres.

**Post-deploy validation (EV-004):** Run H4/H5 connectivity regression on both frontend URLs (AC-F7) — no new API routes, but bundle wiring must include shared workspace packages.

### EV-007 — Invite acceptance redirect chain (F35 ext, #109)

**Browser flow:** GoTrue email link → admin frontend `/accept-invite` or `/reset-password` with hash fragment (`#access_token=…` or `#error=otp_expired`). This is **not** API CORS — it depends on Supabase Auth URL configuration + backend `redirect_to`.

| Variable | App | Purpose |
|----------|-----|---------|
| `VECINITA_ADMIN_FRONTEND_URL` | data-management-modal (DM ASGI) | Build `redirect_to` for invite/resend/recovery GoTrue calls |
| `site_url` | Supabase project (`config.toml` → `config push`) | **Staging-first:** set to staging admin frontend URL (not `localhost:3000`) |
| `additional_redirect_urls` | Supabase project | Full paths: `{staging}/accept-invite`, `{staging}/reset-password`, prod admin URLs, local dev (`127.0.0.1:5173`, etc.) |
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` | data-management-frontend (build) | Unchanged — SPA auth client |

**Redeploy order (EV-007, critical):**

1. **Supabase `config push`** — update `site_url` + `additional_redirect_urls` + template polish (`supabase.yml` on merge to `main`)
2. **Operator verification** — Dashboard → Auth → URL Configuration matches repo (runbook step)
3. **Modal DM backend** — deploy with `VECINITA_ADMIN_FRONTEND_URL` secret
4. **data-management-frontend** — deploy callback handling on `/accept-invite` and `/reset-password`
5. **13-deploy-smoke** — T3 live invite: fresh invite link opens staging `/accept-invite`, password set, login succeeds (H6 browser UJ)

**Connectivity gates:** H4/H5 (API) insufficient alone; **H6** required for invite accept browser journey (T3 deferred from S005).

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
- [ ] **EV-004 (F31):** `coverage` CI job green on `main` — no redeploy; see [staging-runbook.md](staging-runbook.md) §EV-004 coverage gate

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
