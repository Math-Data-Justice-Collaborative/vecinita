"""Database utilities for direct Postgres access."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import uuid4

from vecinita_scraper.core.config import get_config
from vecinita_scraper.core.errors import ConfigError, DatabaseError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.postgres_json_sanitize import (
    sanitize_postgres_json_payload,
    sanitize_postgres_text,
)

logger = get_logger(__name__)

try:
    import psycopg2  # type: ignore[import-untyped]
    from psycopg2.extras import Json, RealDictCursor  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover - exercised only in incomplete environments
    psycopg2 = None
    Json = None
    RealDictCursor = None
    _PSYCOPG2_IMPORT_ERROR: Exception | None = exc
else:
    _PSYCOPG2_IMPORT_ERROR = None

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

T = TypeVar("T")


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _serialize_record(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {key: _serialize_value(value) for key, value in dict(record).items()}


def _serialize_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [record for item in records if (record := _serialize_record(item)) is not None]


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
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def _is_transient_psycopg2_error(exc: BaseException) -> bool:
    """True for errors that often succeed on retry (SSL blips, server closing idle sockets)."""
    msg = str(exc).lower()
    return any(
        s in msg
        for s in (
            "ssl",
            "connection",
            "closed",
            "timeout",
            "server closed",
            "could not connect",
        )
    )


class PostgresDB:
    """Direct Postgres client wrapper for scraper pipeline state."""

    def __init__(self, database_url: str | None = None, connect_timeout: int = 5) -> None:
        config = get_config()
        self.database_url = (database_url or config.postgres.database_url).strip()
        self.connect_timeout = connect_timeout
        if not self.database_url:
            raise DatabaseError(
                "Postgres DSN is required for scraper persistence (DATABASE_URL or DB_URL)"
            )
        if psycopg2 is None or Json is None or RealDictCursor is None:
            raise DatabaseError(
                "psycopg2-binary is not installed. Install project dependencies "
                "before using the database client."
            ) from _PSYCOPG2_IMPORT_ERROR

    async def _run(self, operation: Callable[[], T]) -> T:
        return await asyncio.to_thread(operation)

    def _connect(self) -> Any:
        assert psycopg2 is not None
        assert RealDictCursor is not None
        last_exc: BaseException | None = None
        for attempt in range(3):
            try:
                return psycopg2.connect(
                    self.database_url,
                    connect_timeout=self.connect_timeout,
                    cursor_factory=RealDictCursor,
                )
            except psycopg2.OperationalError as exc:
                last_exc = exc
                if attempt < 2 and _is_transient_psycopg2_error(exc):
                    time.sleep(0.15 * (2**attempt))
                    continue
                raise
        assert last_exc is not None
        raise last_exc

    async def create_scraping_job(
        self,
        url: str,
        user_id: str,
        crawl_config: dict[str, Any],
        chunking_config: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new scraping job and return job_id."""
        job_id = str(uuid4())
        now = datetime.now(UTC)

        def operation() -> None:
            assert Json is not None
            safe_url = sanitize_postgres_text(url)
            safe_user_id = sanitize_postgres_text(user_id)
            safe_crawl = sanitize_postgres_json_payload(crawl_config)
            safe_chunk = sanitize_postgres_json_payload(chunking_config)
            safe_meta = sanitize_postgres_json_payload(metadata or {})
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO scraping_jobs (
                            id,
                            url,
                            user_id,
                            status,
                            crawl_config,
                            chunking_config,
                            metadata,
                            created_at,
                            updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            job_id,
                            safe_url,
                            safe_user_id,
                            "pending",
                            Json(safe_crawl),
                            Json(safe_chunk),
                            Json(safe_meta),
                            now,
                            now,
                        ),
                    )

        try:
            await self._run(operation)
            logger.info("Created scraping job", job_id=job_id, user_id=user_id, url=url)
            return job_id
        except Exception as exc:
            raise DatabaseError(f"Failed to create scraping job: {exc}") from exc

    async def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get the status of a scraping job."""

        def operation() -> dict[str, Any] | None:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        _JOB_DETAIL_SELECT + " WHERE j.id = %s",
                        (job_id,),
                    )
                    return _serialize_record(cursor.fetchone())

        try:
            return await self._run(operation)
        except Exception as exc:
            raise DatabaseError(f"Failed to get job status: {exc}") from exc

    async def list_jobs(self, user_id: str | None = None, limit: int = 50) -> dict[str, Any]:
        """List recent jobs with aggregate counters."""

        def operation() -> dict[str, Any]:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS total
                        FROM scraping_jobs
                        WHERE (%s IS NULL OR user_id = %s)
                        """,
                        (user_id, user_id),
                    )
                    total_row = cursor.fetchone()
                    total = int(total_row["total"] if total_row is not None else 0)

                    cursor.execute(
                        _JOB_DETAIL_SELECT + """
                        WHERE (%s IS NULL OR j.user_id = %s)
                        ORDER BY j.created_at DESC
                        LIMIT %s
                        """,
                        (user_id, user_id, limit),
                    )
                    jobs = _serialize_records(cursor.fetchall())
                    return {"jobs": jobs, "total": total}

        try:
            return await self._run(operation)
        except Exception as exc:
            raise DatabaseError(f"Failed to list jobs: {exc}") from exc

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: str | None = None,
        *,
        pipeline_stage: str | None = None,
        error_category: str | None = None,
    ) -> None:
        """Update job status.

        Optional ``pipeline_stage`` / ``error_category`` merge into ``metadata`` jsonb.
        """
        now = datetime.now(UTC)
        meta_patch: dict[str, Any] = {}
        if pipeline_stage is not None:
            meta_patch["pipeline_stage"] = sanitize_postgres_text(pipeline_stage)
        if error_category is not None:
            meta_patch["error_category"] = sanitize_postgres_text(error_category)

        def operation() -> None:
            assert Json is not None
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    if meta_patch:
                        cursor.execute(
                            """
                            UPDATE scraping_jobs
                            SET status = %s,
                                error_message = %s,
                                updated_at = %s,
                                metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                            WHERE id = %s
                            """,
                            (status, error_message, now, Json(meta_patch), job_id),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE scraping_jobs
                            SET status = %s,
                                error_message = %s,
                                updated_at = %s
                            WHERE id = %s
                            """,
                            (status, error_message, now, job_id),
                        )
                    if cursor.rowcount == 0:
                        raise DatabaseError(
                            "scraping_jobs status update affected 0 rows "
                            f"(job_id={job_id!r} is missing from this database)"
                        )

        try:
            await self._run(operation)
            logger.info("Updated job status", job_id=job_id, status=status)
        except Exception as exc:
            raise DatabaseError(f"Failed to update job status: {exc}") from exc

    async def store_crawled_url(
        self,
        job_id: str,
        url: str,
        raw_content: str,
        content_hash: str,
        status: str = "success",
        error_message: str | None = None,
        *,
        response_kind: str | None = None,
        failure_category: str | None = None,
        operator_summary: str | None = None,
    ) -> str:
        """Upsert crawled URL by (job_id, url) and return stable crawled_url_id.

        Optional outcome fields are accepted for parity with gateway HTTP persistence;
        local Postgres rows only persist ``error_message`` today.
        """
        if any((response_kind, failure_category, operator_summary)):
            logger.debug(
                "Optional crawled_url outcome fields not stored in local Postgres (use gateway)",
                response_kind=response_kind,
                failure_category=failure_category,
                has_operator_summary=bool(operator_summary),
            )
        new_id = str(uuid4())
        crawled_at = datetime.now(UTC)

        def operation() -> str:
            _ = raw_content
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
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
                    row = cursor.fetchone()
                    if row is None or row.get("id") is None:
                        raise DatabaseError(
                            "crawled_urls upsert did not return id "
                            f"(job_id={job_id!r}, url={url!r})"
                        )
                    return str(row["id"])

        try:
            crawled_url_id = await self._run(operation)
            logger.info("Stored crawled URL", job_id=job_id, url=url)
            return crawled_url_id
        except Exception as exc:
            raise DatabaseError(f"Failed to store crawled URL: {exc}") from exc

    async def store_extracted_content(
        self,
        crawled_url_id: str,
        content_type: str,
        raw_content: str,
    ) -> str:
        """Store extracted content and return extracted_content_id."""
        extracted_content_id = str(uuid4())

        def operation() -> None:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
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

        try:
            await self._run(operation)
            logger.info("Stored extracted content", extracted_content_id=extracted_content_id)
            return extracted_content_id
        except Exception as exc:
            raise DatabaseError(f"Failed to store extracted content: {exc}") from exc

    async def store_processed_document(
        self,
        extracted_content_id: str,
        markdown_content: str,
        tables_json: str | None = None,
        metadata_json: str | None = None,
    ) -> str:
        """Store processed document and return processed_doc_id."""
        processed_doc_id = str(uuid4())

        def operation() -> None:
            assert Json is not None
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
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

        try:
            await self._run(operation)
            logger.info("Stored processed document", processed_doc_id=processed_doc_id)
            return processed_doc_id
        except Exception as exc:
            raise DatabaseError(f"Failed to store processed document: {exc}") from exc

    async def store_chunks(self, processed_doc_id: str, chunks: list[dict[str, Any]]) -> list[str]:
        """Store chunks and return list of chunk_ids."""
        chunk_ids = [str(uuid4()) for _ in chunks]

        def operation() -> None:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    for index, chunk in enumerate(chunks):
                        cursor.execute(
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

        try:
            await self._run(operation)
            logger.info("Stored chunks", processed_doc_id=processed_doc_id, count=len(chunk_ids))
            return chunk_ids
        except Exception as exc:
            raise DatabaseError(f"Failed to store chunks: {exc}") from exc

    async def store_embeddings(self, job_id: str, chunk_embeddings: list[dict[str, Any]]) -> None:
        """Store embeddings."""

        def operation() -> None:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    for embedding_data in chunk_embeddings:
                        cursor.execute(
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
                                datetime.now(UTC),
                            ),
                        )

        try:
            await self._run(operation)
            logger.info("Stored embeddings", job_id=job_id, count=len(chunk_embeddings))
        except Exception as exc:
            raise DatabaseError(f"Failed to store embeddings: {exc}") from exc

    async def get_job_chunks_with_embeddings(
        self, job_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get chunks with embeddings for a job."""

        def operation() -> list[dict[str, Any]]:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            c.id AS chunk_id,
                            c.chunk_text AS text,
                            c.position,
                            c.token_count,
                            c.semantic_boundary,
                            e.id AS embedding_id,
                            e.embedding_vector::text AS embedding_vector,
                            e.model_name,
                            e.dimensions,
                            e.created_at,
                            j.url
                        FROM embeddings e
                        JOIN chunks c ON c.id = e.chunk_id
                        JOIN scraping_jobs j ON j.id = e.job_id
                        WHERE e.job_id = %s
                        ORDER BY c.position ASC
                        LIMIT %s OFFSET %s
                        """,
                        (job_id, limit, offset),
                    )
                    rows = cursor.fetchall()

            records = _serialize_records(rows)
            for record in records:
                vector_text = record.pop("embedding_vector", None)
                record["embedding"] = json.loads(vector_text) if vector_text else []
            return records

        try:
            return await self._run(operation)
        except Exception as exc:
            raise DatabaseError(f"Failed to get chunks with embeddings: {exc}") from exc


_db_instance: PostgresDB | None = None
_gateway_http_instance: Any = None


def _scraper_api_key_segments_env() -> list[str]:
    return [p.strip() for p in str(os.getenv("SCRAPER_API_KEYS", "")).split(",") if p.strip()]


def _first_scraper_api_key_env() -> str:
    parts = _scraper_api_key_segments_env()
    return parts[0] if parts else ""


def _use_gateway_http_pipeline() -> bool:
    """When set, workers persist via Render gateway HTTP instead of psycopg2 on Modal."""
    return bool(
        str(os.getenv("SCRAPER_GATEWAY_BASE_URL", "")).strip() and _first_scraper_api_key_env()
    )


def _modal_function_running_in_cloud() -> bool:
    """True inside a Modal remote container (not laptop import / ``modal run`` host process)."""
    try:
        import modal  # noqa: PLC0415

        return not modal.is_local()
    except Exception:
        remote = str(os.getenv("MODAL_IS_REMOTE", "")).strip().lower()
        if remote in {"1", "true", "yes", "on"}:
            return True
        return bool(str(os.getenv("MODAL_TASK_ID", "")).strip())


def _allow_direct_postgres_from_modal_cloud() -> bool:
    """Escape hatch for debugging only; production Modal workers should use the gateway."""
    return str(os.getenv("SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_db() -> PostgresDB | Any:
    """Return Postgres client or gateway HTTP persistence (same async surface for workers)."""
    global _db_instance, _gateway_http_instance
    if _use_gateway_http_pipeline():
        if _gateway_http_instance is None:
            from vecinita_scraper.persistence.gateway_http import GatewayHttpPipelinePersistence

            _gateway_http_instance = GatewayHttpPipelinePersistence(
                base_url=str(os.getenv("SCRAPER_GATEWAY_BASE_URL", "")).strip(),
                token=_first_scraper_api_key_env(),
            )
        return _gateway_http_instance
    if _modal_function_running_in_cloud() and not _allow_direct_postgres_from_modal_cloud():
        raise ConfigError(
            "Modal scraper workers must persist through the Render gateway (HTTP), not a direct "
            "Postgres connection from Modal. Set SCRAPER_GATEWAY_BASE_URL to the gateway public "
            "base URL and SCRAPER_API_KEYS (comma-separated; the first segment is sent as the "
            "pipeline ingest header token; the gateway must list the same key set). You can omit "
            "MODAL_DATABASE_URL / DATABASE_URL on Modal for pipeline-only workers when this pair "
            "is set. See docs/deployment/RENDER_SHARED_ENV_CONTRACT.md. "
            "For exceptional debugging only, set SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL=1."
        )
    if _db_instance is None:
        _db_instance = PostgresDB()
    return _db_instance


def set_db(db: PostgresDB | Any | None) -> None:
    """Set database instance (for testing)."""
    global _db_instance, _gateway_http_instance
    _db_instance = db
    _gateway_http_instance = None
