"""Postgres persistence for Modal scraper **control-plane** jobs on the Render gateway.

When ``MODAL_SCRAPER_PERSIST_VIA_GATEWAY`` is enabled, the gateway inserts/reads/updates
``scraping_jobs`` here and Modal ``modal_scrape_job_submit`` only enqueues work.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.utils.database_url import get_resolved_database_url

try:
    import psycopg2  # type: ignore[import-untyped]
    from psycopg2.extras import Json, RealDictCursor  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    psycopg2 = None
    Json = None
    RealDictCursor = None

_JOB_DETAIL_SELECT = """
    SELECT
        j.id,
        j.user_id,
        j.url,
        j.status,
        j.crawl_config,
        j.chunking_config,
        j.metadata,
        j.error_message,
        j.created_at,
        j.updated_at,
        (
            SELECT COUNT(*)
            FROM crawled_urls cu
            WHERE cu.job_id = j.id
        ) AS crawl_url_count,
        (
            SELECT COUNT(*)
            FROM chunks c
            JOIN processed_documents pd ON pd.id = c.processed_doc_id
            JOIN extracted_content ec ON ec.id = pd.extracted_content_id
            JOIN crawled_urls cu ON cu.id = ec.crawled_url_id
            WHERE cu.job_id = j.id
        ) AS chunk_count,
        (
            SELECT COUNT(*)
            FROM embeddings e
            WHERE e.job_id = j.id
        ) AS embedding_count
    FROM scraping_jobs j
"""

_STATUS_TO_PROGRESS: dict[str, int] = {
    "pending": 5,
    "validating": 10,
    "crawling": 20,
    "extracting": 35,
    "processing": 50,
    "chunking": 65,
    "embedding": 80,
    "storing": 95,
    "completed": 100,
    "failed": 0,
    "cancelled": 0,
}

_NON_CANCELLABLE = frozenset({"completed", "failed", "cancelled"})


def _database_url() -> str:
    url = get_resolved_database_url().strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL (or DB_URL) is required for gateway-owned scraper persistence"
        )
    return url


def _connect() -> Any:
    if psycopg2 is None or RealDictCursor is None or Json is None:
        raise RuntimeError("psycopg2 is required for gateway-owned scraper persistence")
    return psycopg2.connect(
        _database_url(),
        connect_timeout=5,
        cursor_factory=RealDictCursor,
    )


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    return value


def _serialize_record(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {k: _serialize_value(v) for k, v in dict(record).items()}


def _serialize_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [r for row in records if (r := _serialize_record(row)) is not None]


def create_scraping_job(
    *,
    url: str,
    user_id: str,
    crawl_config: dict[str, Any],
    chunking_config: dict[str, Any],
    metadata: dict[str, Any] | None,
) -> str:
    """Insert a ``scraping_jobs`` row and return its id (UUID string)."""
    assert Json is not None
    job_id = str(uuid4())
    now = datetime.now(timezone.utc)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO scraping_jobs (
                    id, url, user_id, status,
                    crawl_config, chunking_config, metadata,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    job_id,
                    url,
                    user_id,
                    "pending",
                    Json(crawl_config),
                    Json(chunking_config),
                    Json(metadata or {}),
                    now,
                    now,
                ),
            )
    return job_id


def fetch_job_detail(job_id: str) -> dict[str, Any] | None:
    """Return one serialized job row (``id`` + aggregates) or ``None``."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(_JOB_DETAIL_SELECT + " WHERE j.id = %s", (job_id,))
            row = cur.fetchone()
    return _serialize_record(row)


def job_status_payload(job_id: str) -> dict[str, Any] | None:
    """Shape compatible with gateway ``GatewayModalScrapeJobBody`` / Modal envelope ``data``."""
    row = fetch_job_detail(job_id)
    if not row:
        return None
    status = str(row.get("status") or "pending")
    progress = _STATUS_TO_PROGRESS.get(status, 0)
    created = row.get("created_at")
    updated = row.get("updated_at")
    return {
        "job_id": job_id,
        "id": job_id,
        "status": status,
        "progress_pct": progress,
        "current_step": status,
        "error_message": row.get("error_message"),
        "updated_at": updated,
        "created_at": created,
        "crawl_url_count": int(row.get("crawl_url_count") or 0),
        "chunk_count": int(row.get("chunk_count") or 0),
        "embedding_count": int(row.get("embedding_count") or 0),
    }


def list_jobs_payload(*, user_id: str | None, limit: int) -> dict[str, Any]:
    """Return ``{"jobs": [...], "total": n}`` aligned with Modal list envelope."""
    lim = max(1, min(100, int(limit)))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM scraping_jobs
                WHERE (%s IS NULL OR user_id = %s)
                """,
                (user_id, user_id),
            )
            total_row = cur.fetchone()
            total = int(total_row["total"] if total_row is not None else 0)

            cur.execute(
                _JOB_DETAIL_SELECT + """
                WHERE (%s IS NULL OR j.user_id = %s)
                ORDER BY j.created_at DESC
                LIMIT %s
                """,
                (user_id, user_id, lim),
            )
            raw_jobs = cur.fetchall()
    jobs = _serialize_records(raw_jobs)
    return {"jobs": jobs, "total": total}


def cancel_job(job_id: str) -> tuple[dict[str, Any] | None, str | None]:
    """Cancel job on Render. Returns ``(payload, None)`` or ``(None, "not_found"|"conflict")``."""
    row = fetch_job_detail(job_id)
    if not row:
        return None, "not_found"
    status = str(row.get("status") or "pending")
    if status in _NON_CANCELLABLE:
        return None, "conflict"
    now = datetime.now(timezone.utc)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE scraping_jobs
                SET status = %s, error_message = %s, updated_at = %s
                WHERE id = %s
                """,
                ("cancelled", None, now, job_id),
            )
    out = job_status_payload(job_id)
    if out is None:
        return None, "not_found"
    out["previous_status"] = status
    out["new_status"] = "cancelled"
    return out, None
