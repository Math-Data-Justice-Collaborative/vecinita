-- =============================================================================
-- Migration 003: Active crawl append-only audit tables (spec 008)
-- Idempotent: IF NOT EXISTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS crawl_runs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    started_at        TIMESTAMPTZ NOT NULL DEFAULT TIMEZONE('utc', NOW()),
    finished_at       TIMESTAMPTZ,
    status              TEXT NOT NULL DEFAULT 'running',
    config_snapshot     JSONB NOT NULL DEFAULT '{}'::jsonb,
    pages_fetched       INTEGER NOT NULL DEFAULT 0,
    pages_skipped       INTEGER NOT NULL DEFAULT 0,
    pages_failed        INTEGER NOT NULL DEFAULT 0,
    initiator           TEXT,
    notes               TEXT,
    CONSTRAINT crawl_runs_status_check CHECK (
        status IN ('running', 'completed', 'failed', 'cancelled')
    )
);

CREATE TABLE IF NOT EXISTS crawl_fetch_attempts (
    id                    BIGSERIAL PRIMARY KEY,
    crawl_run_id          UUID NOT NULL REFERENCES crawl_runs (id) ON DELETE CASCADE,
    canonical_url         TEXT NOT NULL,
    requested_url         TEXT NOT NULL,
    final_url             TEXT,
    seed_root             TEXT NOT NULL,
    depth                 INTEGER NOT NULL DEFAULT 0,
    attempted_at          TIMESTAMPTZ NOT NULL DEFAULT TIMEZONE('utc', NOW()),
    http_status           INTEGER,
    outcome               TEXT NOT NULL,
    skip_reason           TEXT,
    retrieval_path        TEXT NOT NULL,
    document_format       TEXT,
    extracted_text        TEXT,
    raw_artifact          BYTEA,
    raw_omitted_reason    TEXT,
    content_sha256        TEXT,
    pdf_extraction_status TEXT,
    error_detail          TEXT,
    CONSTRAINT crawl_fetch_attempts_outcome_check CHECK (
        outcome IN ('success', 'partial', 'failed', 'skipped')
    )
);

CREATE INDEX IF NOT EXISTS idx_crawl_fetch_attempts_run_time
    ON crawl_fetch_attempts (crawl_run_id, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_crawl_fetch_attempts_canonical_time
    ON crawl_fetch_attempts (canonical_url, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_crawl_fetch_attempts_seed_run
    ON crawl_fetch_attempts (seed_root, crawl_run_id);
