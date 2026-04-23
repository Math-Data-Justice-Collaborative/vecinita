-- Active crawl inspection (spec 008). Run with:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/validate_active_crawl.sql

SELECT id, started_at, finished_at, status,
       pages_fetched, pages_skipped, pages_failed, initiator
FROM crawl_runs
ORDER BY started_at DESC
LIMIT 10;

WITH latest AS (
    SELECT id FROM crawl_runs ORDER BY started_at DESC LIMIT 1
)
SELECT f.crawl_run_id, f.canonical_url, f.depth, f.outcome, f.skip_reason,
       f.retrieval_path, f.document_format, f.pdf_extraction_status,
       f.attempted_at
FROM crawl_fetch_attempts f
WHERE f.crawl_run_id IN (SELECT id FROM latest)
ORDER BY f.attempted_at DESC
LIMIT 25;
