"""Render Postgres writes for Modal scraper **pipeline** stages (crawl → embed).

Called only from gateway internal HTTP routes; Modal workers POST payloads here instead of
opening a DSN on Modal.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.services.ingestion import pipeline_stage as pipeline_stage_rules
from src.utils.database_url import get_resolved_database_url
from src.utils.postgres_json_sanitize import sanitize_postgres_json_payload, sanitize_postgres_text

try:
    import psycopg2  # type: ignore[import-untyped]
    from psycopg2.extras import Json, RealDictCursor  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    psycopg2 = None
    Json = None
    RealDictCursor = None


def _reraise_psycopg_sanitized(exc: BaseException) -> None:
    if psycopg2 is not None and isinstance(exc, psycopg2.Error):
        from src.utils.gateway_dependency_errors import client_safe_message_for_dependency_failure

        raise RuntimeError(client_safe_message_for_dependency_failure(exc)) from exc
    raise exc


def _database_url() -> str:
    url = get_resolved_database_url().strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL (or DB_URL) is required for scraper pipeline ingest persistence"
        )
    return url


def _connect() -> Any:
    if psycopg2 is None or RealDictCursor is None or Json is None:
        raise RuntimeError("psycopg2 is required for scraper pipeline ingest persistence")
    return psycopg2.connect(
        _database_url(),
        connect_timeout=5,
        cursor_factory=RealDictCursor,
    )


def _parse_json_text(value: str | None) -> Any:
    if value is None or value == "":
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _json_value_for_postgres(raw: Any) -> Any:
    """Prepare a value for ``psycopg2.extras.Json`` so Postgres json/jsonb accepts it."""
    if isinstance(raw, (dict, list)):
        return sanitize_postgres_json_payload(raw)
    if isinstance(raw, str):
        return sanitize_postgres_text(raw)
    return raw


def _vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in values) + "]"


def _decorate_error_message(error_message: str | None, error_category: str | None) -> str | None:
    """Prefix operator-safe messages with ``[category]`` when ``error_category`` is set."""
    if not error_message or not error_category:
        return error_message
    cat = sanitize_postgres_text(error_category)
    msg = sanitize_postgres_text(error_message)
    bracket = f"[{cat}]"
    if msg.startswith(bracket):
        return msg
    return f"{bracket} {msg}"


def update_job_status(
    job_id: str,
    status: str,
    error_message: str | None = None,
    *,
    pipeline_stage: str | None = None,
    error_category: str | None = None,
) -> None:
    """Update ``scraping_jobs.status``; optionally merge ``pipeline_stage`` / ``error_category`` into ``metadata`` jsonb.

    When ``pipeline_stage`` is provided, transitions are validated against the prior
    ``metadata.pipeline_stage`` (defaulting from **queued** when unset). Legacy workers
    that only send ``status`` remain supported (no metadata read).
    """
    now = datetime.now(timezone.utc)
    eff_message = _decorate_error_message(error_message, error_category)
    if pipeline_stage is None and error_category is None:
        try:
            with _connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE scraping_jobs
                        SET status = %s,
                            error_message = %s,
                            updated_at = %s
                        WHERE id = %s
                        """,
                        (status, eff_message, now, job_id),
                    )
                    if cur.rowcount == 0:
                        raise RuntimeError(
                            "scraping_jobs status update affected 0 rows "
                            f"(job_id={job_id!r} is missing from this database)"
                        )
        except Exception as exc:
            _reraise_psycopg_sanitized(exc)
        return

    if Json is None:
        raise RuntimeError("psycopg2.extras.Json is required for pipeline metadata updates")

    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT metadata FROM scraping_jobs WHERE id = %s FOR UPDATE",
                    (job_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError(
                        "scraping_jobs status update affected 0 rows "
                        f"(job_id={job_id!r} is missing from this database)"
                    )
                raw_meta = row.get("metadata")
                meta: dict[str, Any] = (
                    dict(raw_meta)
                    if isinstance(raw_meta, dict)
                    else _parse_json_text(raw_meta) or {}
                )
                meta = sanitize_postgres_json_payload(meta)
                if pipeline_stage is not None:
                    prev = meta.get("pipeline_stage")
                    before = (
                        str(prev).strip()
                        if isinstance(prev, str) and prev.strip()
                        else pipeline_stage_rules.PIPELINE_STAGE_QUEUED
                    )
                    pipeline_stage_rules.validate_pipeline_stage_transition(before, pipeline_stage)
                    meta["pipeline_stage"] = sanitize_postgres_text(pipeline_stage)
                    meta["pipeline_stage_updated_at"] = now.isoformat()
                if error_category is not None:
                    meta["error_category"] = sanitize_postgres_text(error_category)

                cur.execute(
                    """
                    UPDATE scraping_jobs
                    SET status = %s,
                        error_message = %s,
                        metadata = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (status, eff_message, Json(meta), now, job_id),
                )
                if cur.rowcount == 0:
                    raise RuntimeError(
                        "scraping_jobs status update affected 0 rows "
                        f"(job_id={job_id!r} is missing from this database)"
                    )
    except ValueError:
        raise
    except Exception as exc:
        _reraise_psycopg_sanitized(exc)


def store_crawled_url(
    job_id: str,
    url: str,
    raw_content: str,
    content_hash: str,
    status: str = "success",
    error_message: str | None = None,
) -> str:
    """Upsert crawled_urls by (job_id, url); return stable ``id``.

    Idempotent for Modal retries and duplicate ingest calls. ``raw_content`` is accepted for API
    parity but not stored.
    """
    _ = raw_content
    new_id = str(uuid4())
    crawled_at = datetime.now(timezone.utc)
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO crawled_urls (
                        id,
                        job_id,
                        url,
                        raw_content_hash,
                        status,
                        error_message,
                        crawled_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id, url) DO UPDATE SET
                        raw_content_hash = EXCLUDED.raw_content_hash,
                        status = EXCLUDED.status,
                        error_message = EXCLUDED.error_message,
                        crawled_at = EXCLUDED.crawled_at
                    RETURNING id
                    """,
                    (
                        new_id,
                        job_id,
                        url,
                        content_hash,
                        status,
                        error_message,
                        crawled_at,
                    ),
                )
                row = cur.fetchone()
                if row is None or row.get("id") is None:
                    raise RuntimeError(
                        f"crawled_urls upsert did not return id (job_id={job_id!r}, url={url!r})"
                    )
                return str(row["id"])
    except Exception as exc:
        _reraise_psycopg_sanitized(exc)


def store_extracted_content(
    crawled_url_id: str,
    content_type: str,
    raw_content: str,
) -> str:
    extracted_content_id = str(uuid4())
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO extracted_content (
                        id,
                        crawled_url_id,
                        content_type,
                        raw_content,
                        processing_status
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        extracted_content_id,
                        crawled_url_id,
                        content_type,
                        raw_content,
                        "pending",
                    ),
                )
    except Exception as exc:
        _reraise_psycopg_sanitized(exc)
    return extracted_content_id


def store_processed_document(
    extracted_content_id: str,
    markdown_content: str,
    tables_json: str | None = None,
    metadata_json: str | None = None,
) -> str:
    assert Json is not None
    processed_doc_id = str(uuid4())
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO processed_documents (
                        id,
                        extracted_content_id,
                        markdown_content,
                        tables_json,
                        metadata_json
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        processed_doc_id,
                        extracted_content_id,
                        markdown_content,
                        tables_json,
                        (
                            Json(_json_value_for_postgres(_parse_json_text(metadata_json)))
                            if metadata_json is not None
                            else None
                        ),
                    ),
                )
    except Exception as exc:
        _reraise_psycopg_sanitized(exc)
    return processed_doc_id


def store_chunks(processed_doc_id: str, chunks: list[dict[str, Any]]) -> list[str]:
    chunk_ids = [str(uuid4()) for _ in chunks]
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                for index, chunk in enumerate(chunks):
                    text_main = chunk["text"]
                    raw_t = chunk.get("raw_text") or text_main
                    enriched = chunk.get("enriched_text")
                    cur.execute(
                        """
                        INSERT INTO chunks (
                            id,
                            processed_doc_id,
                            chunk_text,
                            position,
                            token_count,
                            semantic_boundary,
                            raw_text,
                            enriched_text
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            chunk_ids[index],
                            processed_doc_id,
                            text_main,
                            chunk.get("position", index),
                            chunk.get("token_count", 0),
                            chunk.get("semantic_boundary", False),
                            raw_t,
                            enriched,
                        ),
                    )
    except Exception as exc:
        _reraise_psycopg_sanitized(exc)
    return chunk_ids


def store_embeddings(job_id: str, chunk_embeddings: list[dict[str, Any]]) -> None:
    """Insert embedding rows; each item must include ``chunk_id`` and ``embedding`` (list of float)."""
    now = datetime.now(timezone.utc)
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                for embedding_data in chunk_embeddings:
                    cur.execute(
                        """
                        INSERT INTO embeddings (
                            id,
                            job_id,
                            chunk_id,
                            embedding_vector,
                            model_name,
                            dimensions,
                            created_at
                        ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s)
                        ON CONFLICT (chunk_id, model_name) DO NOTHING
                        """,
                        (
                            str(uuid4()),
                            job_id,
                            embedding_data["chunk_id"],
                            _vector_literal(embedding_data["embedding"]),
                            embedding_data.get("model_name", "BAAI/bge-small-en-v1.5"),
                            embedding_data.get("dimensions", 384),
                            now,
                        ),
                    )
    except Exception as exc:
        _reraise_psycopg_sanitized(exc)
