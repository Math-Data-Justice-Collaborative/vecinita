# Contract: Render gateway ↔ Modal workers (pipeline persistence)

## Purpose

Document **connection points** between **Render** (gateway + Postgres) and **Modal** (scraper / pipeline workers) so env vars and tokens stay aligned with **FR-012** / **FR-013**. Canonical detail also lives in `docs/deployment/MODAL_DEPLOYMENT.md` and `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` — **update those** when this feature changes wire-up.

## Topology

```text
Browser ──HTTPS──► Render: vecinita-gateway (public)
                       │
                       ├── Modal SDK ──► Modal: scraper / pipeline functions
                       │
                       └── Postgres (DATABASE_URL)

Modal worker ──HTTPS──► Render: vecinita-gateway
            POST /api/v1/internal/scraper-pipeline/...
            Header: X-Scraper-Pipeline-Ingest-Token: <secret>
```

**FR-013**: Only **gateway** and **co-released** worker processes (same release train as gateway—typically Modal app deployed from `services/scraper` revision paired in CI/docs) invoke Modal for scrape/embed/LLM stages of **this** pipeline. No third Render web service introduces parallel Modal callers for the same steps without a spec amendment.

## Required / referenced environment variables

| Variable | Owner | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | Render gateway | Pipeline persist modules (`modal_scraper_pipeline_persist`) require DSN on gateway. |
| `SCRAPER_GATEWAY_BASE_URL` | Modal scraper env | Public base URL of gateway for worker HTTP persistence. |
| `SCRAPER_API_KEYS` | Gateway + Modal | Shared allowlist; worker sends token for internal pipeline routes. |
| `MODAL_FUNCTION_INVOCATION` / Modal tokens | Gateway (and agent where applicable) | SDK invocation to Modal; never exposed to browser. |
| Frontend `VITE_*` | Render static site | **Single** API base pointing at **gateway** for chat/ingestion features per **FR-012**; DM SPA continues DM API base per **007** matrix. |

## Pipeline stage persistence (normative — resolves analyze **A1**)

**Decision (v1):** Persist **`pipeline_stage`**, **`error_category`**, and related operator fields using **structured data in existing rows** first—e.g. `scraping_jobs.metadata` jsonb and/or a documented prefix in `error_message`—so Modal workers and gateway stays backward-compatible without blocking on DDL. **Only** introduce new SQL columns under `services/scraper/migrations/` when profiling or operator UX requires indexed queries on those fields; then run the explicit migration task (see **T018** in `tasks.md`) and bump contract notes here.

## Internal pipeline ingest (server-to-server)

- **Path prefix**: `/api/v1/internal/scraper-pipeline` (see `router_scraper_pipeline_ingest.py`).  
- **Auth**: Shared secret header; gateway validates before touching Postgres.  
- **Payloads**: JSON bodies for stage completion; must remain backward-compatible or versioned.

## Failure behavior

- Modal **cannot** reach gateway (DNS, 401, 5xx): worker MUST retry with backoff; terminal fail updates job status via alternative path or DLQ policy (tasks).  
- Gateway maps **browser-visible** errors per **gateway-ingestion-http-surface.md**; internal ingest errors are **not** browser-visible.

## Acceptance checks

1. Staging: Modal worker completes crawl and **successfully POSTs** at least one pipeline stage; rows visible in Postgres with same `job_id`.  
2. Mis-set `SCRAPER_GATEWAY_BASE_URL`: job fails fast with **classified** error (no silent success).  
3. Token mismatch: **401** on internal routes; no DB writes.
