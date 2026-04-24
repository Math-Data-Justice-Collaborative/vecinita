# Quickstart — operators & developers (009)

## Operator: fix “must persist through the Render gateway” on Modal

1. Open **`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`** → section **Gateway HTTP pipeline ingest** and the **Go / no-go checklist** table.
2. On **Render** (`vecinita-gateway`), confirm **`SCRAPER_API_KEYS`** is set (comma-separated secrets).
3. On **Modal** secret group **`vecinita-scraper-env`**, set:
   - **`SCRAPER_GATEWAY_BASE_URL`** — public origin of the gateway (e.g. `https://…onrender.com`, no trailing path).
   - **`SCRAPER_API_KEYS`** — **exact same string** as on the gateway (first non-empty segment is sent as pipeline ingest token).
4. For pipeline-only workers, you may **remove** `MODAL_DATABASE_URL` / `DATABASE_URL` from Modal once the pair above is correct (per contract).
5. Redeploy Modal app / bump workers; rerun a single scrape job and confirm logs no longer show the `ConfigError`.

## Developer: reproduce locally

From repo root, prefer the scraper Makefile (uses Python 3.11 + project deps):

```bash
cd services/scraper
make test-unit
```

Focused regression modules for this feature:

```bash
cd services/scraper
make test-unit  # or: pytest tests/unit/test_get_db_modal_gateway.py tests/unit/test_worker_failure_paths.py -q
```

Contract matrix: [contracts/modal-get-db-persistence-matrix.md](./contracts/modal-get-db-persistence-matrix.md).

## CI regression coverage (gateway + scraper)

- **Gateway job_id submit / gateway persist:** `backend/tests/test_api/test_router_modal_jobs.py` (e.g. `test_modal_scraper_submit_gateway_persist_injects_job_id`).
- **Pipeline ingest token (any key segment):** `backend/tests/test_api/test_router_scraper_pipeline_ingest.py` (e.g. `test_pipeline_ingest_accepts_any_listed_api_key`).
- **Modal worker `get_db()` matrix + failure helper:** `services/scraper/tests/unit/test_get_db_modal_gateway.py`, `services/scraper/tests/unit/test_worker_failure_paths.py`.

Full monorepo gate: `make ci` from the vecinita repository root.

## Exceptional debugging only

Set **`SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL=1`** on Modal **only** with explicit approval and remove after debugging. Never rely on this for production pipeline throughput. See **`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`** (same section as gateway HTTP ingest) for the operator-facing policy paragraph.
