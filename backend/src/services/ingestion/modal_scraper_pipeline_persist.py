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


def update_job_status(
    job_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    now = datetime.now(timezone.utc)
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
                    (status, error_message, now, job_id),
                )
                if cur.rowcount == 0:
                    raise RuntimeError(
                        "scraping_jobs status update affected 0 rows "
                        f"(job_id={job_id!r} is missing from this database)"
                    )
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
    """Insert crawled_urls row; ``raw_content`` is accepted for API parity but not stored."""
    _ = raw_content
    crawled_url_id = str(uuid4())
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
                    """,
                    (
                        crawled_url_id,
                        job_id,
                        url,
                        content_hash,
                        status,
                        error_message,
                        crawled_at,
                    ),
                )
    except Exception as exc:
        _reraise_psycopg_sanitized(exc)
    return crawled_url_id


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
                    cur.execute(
                        """
                        INSERT INTO chunks (
                            id,
                            processed_doc_id,
                            chunk_text,
                            position,
                            token_count,
                            semantic_boundary
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            chunk_ids[index],
                            processed_doc_id,
                            chunk["text"],
                            chunk.get("position", index),
                            chunk.get("token_count", 0),
                            chunk.get("semantic_boundary", False),
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
