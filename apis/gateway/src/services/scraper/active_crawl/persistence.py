"""Append-only Postgres persistence for crawl_runs / crawl_fetch_attempts."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from src.utils.database_url import get_resolved_database_url

log = logging.getLogger("vecinita_pipeline.active_crawl.persistence")

try:
    import psycopg2
    import psycopg2.extensions

    PSYCOPG2 = True
except Exception:  # pragma: no cover - optional in minimal envs
    psycopg2 = None  # type: ignore[assignment]
    PSYCOPG2 = False


@dataclass
class FetchAttemptRow:
    crawl_run_id: UUID
    canonical_url: str
    requested_url: str
    final_url: str | None
    seed_root: str
    depth: int
    http_status: int | None
    outcome: str
    skip_reason: str | None
    retrieval_path: str
    document_format: str | None
    extracted_text: str | None
    raw_artifact: bytes | None
    raw_omitted_reason: str | None
    content_sha256: str | None
    pdf_extraction_status: str | None
    error_detail: str | None


class CrawlRepository:
    """Insert-only helpers for active crawl tables."""

    def __init__(self, database_url: str | None = None) -> None:
        self._url = database_url or get_resolved_database_url()
        if not self._url:
            raise RuntimeError("DATABASE_URL (or DB_URL) is required for active crawl persistence")
        if not PSYCOPG2:
            raise RuntimeError("psycopg2 is required for active crawl persistence")

    def _conn(self) -> Any:
        return psycopg2.connect(self._url)

    def create_run(self, config_snapshot: dict[str, Any], initiator: str = "cli") -> UUID:
        sql = """
            INSERT INTO crawl_runs (status, config_snapshot, initiator)
            VALUES ('running', %s::jsonb, %s)
            RETURNING id
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (json.dumps(config_snapshot), initiator))
                row = cur.fetchone()
                conn.commit()
        rid = row[0]
        log.info("Created crawl_run id=%s", rid)
        return UUID(str(rid))

    def increment_counters(
        self,
        run_id: UUID,
        *,
        fetched: int = 0,
        skipped: int = 0,
        failed: int = 0,
    ) -> None:
        sql = """
            UPDATE crawl_runs
            SET pages_fetched = pages_fetched + %s,
                pages_skipped = pages_skipped + %s,
                pages_failed = pages_failed + %s
            WHERE id = %s
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (fetched, skipped, failed, str(run_id)))
            conn.commit()

    def finish_run(
        self,
        run_id: UUID,
        status: str,
        notes: str | None = None,
    ) -> None:
        sql = """
            UPDATE crawl_runs
            SET status = %s,
                finished_at = TIMEZONE('utc', NOW()),
                notes = COALESCE(%s, notes)
            WHERE id = %s
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (status, notes, str(run_id)))
            conn.commit()

    def get_run_summary(self, run_id: UUID) -> dict[str, Any]:
        sql = """
            SELECT status, pages_fetched, pages_skipped, pages_failed
            FROM crawl_runs
            WHERE id = %s
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (str(run_id),))
                row = cur.fetchone()
        if not row:
            raise KeyError(f"crawl_run not found: {run_id}")
        return {
            "status": row[0],
            "pages_fetched": int(row[1] or 0),
            "pages_skipped": int(row[2] or 0),
            "pages_failed": int(row[3] or 0),
        }

    def insert_fetch_attempt(self, row: FetchAttemptRow) -> None:
        sql = """
            INSERT INTO crawl_fetch_attempts (
                crawl_run_id, canonical_url, requested_url, final_url, seed_root, depth,
                attempted_at, http_status, outcome, skip_reason, retrieval_path,
                document_format, extracted_text, raw_artifact, raw_omitted_reason,
                content_sha256, pdf_extraction_status, error_detail
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        attempted = datetime.now(timezone.utc)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        str(row.crawl_run_id),
                        row.canonical_url,
                        row.requested_url,
                        row.final_url,
                        row.seed_root,
                        row.depth,
                        attempted,
                        row.http_status,
                        row.outcome,
                        row.skip_reason,
                        row.retrieval_path,
                        row.document_format,
                        row.extracted_text,
                        row.raw_artifact,
                        row.raw_omitted_reason,
                        row.content_sha256,
                        row.pdf_extraction_status,
                        row.error_detail,
                    ),
                )
            conn.commit()
