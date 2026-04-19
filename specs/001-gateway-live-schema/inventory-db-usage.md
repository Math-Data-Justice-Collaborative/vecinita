# Inventory: Postgres / DSN usage (Modal vs Render)

**Feature:** `001-gateway-live-schema`  
**Last updated:** 2026-04-18

## Render (gateway / agent)

| Area | Path / module | Env | Notes |
|------|----------------|-----|-------|
| Gateway Modal job control (optional path) | `backend/src/services/ingestion/modal_scraper_persist.py` | `DATABASE_URL` / `DB_URL` via `get_resolved_database_url()` | Used when **`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`** is set on the gateway. |
| Gateway documents / agent | `backend/src/api/router_documents.py`, `backend/src/agent/main.py`, … | `DATABASE_URL` | Existing Render-owned persistence. |
| Modal invoker | `backend/src/services/modal/invoker.py` | — | **No** DB; `Function.from_name` RPC only. |

## Modal (scraper service)

| Area | Path / module | Env | Notes |
|------|----------------|-----|-------|
| Job control plane (legacy) | `services/scraper/src/vecinita_scraper/services/job_control.py` → `PostgresDB` | `DATABASE_URL`, `MODAL_DATABASE_URL` (see `vecinita_scraper.core.config`) | **Default:** create/list/get/cancel scraping jobs in Postgres **from Modal**. |
| Job control plane (gateway-owned) | Same module | **`MODAL_SCRAPER_PERSIST_VIA_GATEWAY=1`** | **Submit:** skips `PostgresDB.create_scraping_job` when `job_id` is present on the request; **enqueue only**. Modal **must not** receive internal-only `dpg-*-a` URLs for worker stages that still open DB (see plan / worker follow-up). |
| Workers (crawl / pipeline) | `services/scraper/src/vecinita_scraper/workers/*.py`, `core/db.py` | Same DSN vars | Still use Postgres today for pipeline state; migrating workers off DB is **out of band** for control-plane RPC tasks (T007 scope). |

## Backend tests / hooks

| Area | Path | Notes |
|------|------|-------|
| Schemathesis hooks | `backend/tests/schemathesis_hooks.py` | No DB; seeds path/query params. |
