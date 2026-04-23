# Quickstart: Active crawl CLI

## Prerequisites

1. Repo root `.env` with valid **`DATABASE_URL`**.  
2. Apply DB migration **`backend/scripts/migrations/003_active_crawl_tables.sql`** (creates **`crawl_runs`** / **`crawl_fetch_attempts`** with indexes `idx_crawl_fetch_attempts_run_time`, `idx_crawl_fetch_attempts_canonical_time`, `idx_crawl_fetch_attempts_seed_run`).  
3. For Playwright-backed URLs:  
   ```bash
   cd backend && uv sync --extra scraping && uv run playwright install
   ```

## Run

```bash
# From repo root (after implementation)
make active-crawl
# or
./scripts/run_active_crawl.sh --verbose
# underlying invocation (from backend/, same as existing scraper CLI)
# uv run python -m src.services.scraper.active_crawl --help
```

## Inspect results

```sql
-- Latest runs
SELECT id, started_at, finished_at, status, pages_fetched, pages_failed
FROM crawl_runs
ORDER BY started_at DESC
LIMIT 10;

-- Attempts for one run
SELECT canonical_url, outcome, retrieval_path, http_status, skip_reason, LEFT(extracted_text, 80)
FROM crawl_fetch_attempts
WHERE crawl_run_id = '<paste-id>'
ORDER BY attempted_at;
```

Use **`contracts/crawl-persistence-schema.md`** for the “latest successful per URL” reference query.

## SC-002 acceptance (staging / manual)

Spec **SC-002** expects that, for a **standard subset of ≥5 hosts** (mix of static and script-heavy), **about 90%** of reachable in-scope pages under default caps end up with **extractable text** or a **specific non-success reason** in `crawl_fetch_attempts`.

- **Automated slice**: **`T030`** (`ACCEPTANCE_SEEDS.md` + `test_sc002_acceptance_seeds.py`) validates the **host list file**, not live crawl success rates.  
- **Full SC-002**: Run a **capped** `make active-crawl` in staging (or against a fixture stack), then SQL-check the fraction of rows with `outcome` / `extracted_text` / explicit `skip_reason` / `error_detail`. Record results in your release notes or a short runbook entry. **CI** may skip full SC-002 unless you add an optional gated job (out of scope for the default task list).

## Seeds

Edit **`data/config/active_crawl_seeds.txt`** (after implementation lands) or rely on merged lists from `ScraperConfig`; fix obvious hostname typos before production crawls.

## Relationship to existing `make scraper-run`

- **`make scraper-run`**: existing batch pipeline → chunks / vector sync.  
- **`make active-crawl`**: new bounded crawl + **append-only** fetch history tables.  
Later tasks may chain: active crawl → feed selected URLs into `VecinaScraper` for chunking.

## Validation targets (FR-009)

Do not confuse the two Postgres inspection entry points:

| Make target | What it checks |
|-------------|----------------|
| **`make scraper-validate-postgres`** | Existing pipeline: **`document_chunks`** (and related validation in `scripts/run_scraper_postgres_batch.sh`). |
| **`make active-crawl-validate`** | New crawl audit tables: **`crawl_runs`** / **`crawl_fetch_attempts`** via **`scripts/validate_active_crawl.sh`** (runs **`scripts/validate_active_crawl.sql`**). |

Use the target that matches the data you just wrote.
