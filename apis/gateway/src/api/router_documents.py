"""
Public Documents Router

Read-only, unauthenticated endpoints that power the public Documents Dashboard.
Exposes corpus metadata: embedding model, chunk stats, source list, and chunk previews.
No auth required — all data is non-sensitive metadata about the public knowledge base.
"""

import json
import logging
import os
from typing import Annotated, Any, cast
from urllib.parse import quote, urlparse

import psycopg2  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor  # type: ignore[import-untyped]

from src.config import EMBEDDING_SERVICE_URL as _CONFIG_EMBEDDING_SERVICE_URL
from src.services.corpus.corpus_projection_service import should_fail_closed_for_projection_error
from src.utils.database_url import get_resolved_database_url
from src.utils.tags import build_bilingual_tag_fields, normalize_tags

from .models import (
    DocumentsChunkStatisticsQueryParams,
    DocumentsChunkStatisticsResponse,
    DocumentsChunkStatisticsRow,
    DocumentsDownloadUrlQueryParams,
    DocumentsDownloadUrlResponse,
    DocumentsOverviewQueryParams,
    DocumentsOverviewResponse,
    DocumentsPreviewChunk,
    DocumentsPreviewQueryParams,
    DocumentsPreviewResponse,
    DocumentsTagRow,
    DocumentsTagsQueryParams,
    DocumentsTagsResponse,
    PublicDocumentsSourceItem,
)


def _pg_connect(*args: Any, **kwargs: Any):  # noqa: ANN401
    """Thin wrapper so integration tests can monkeypatch DB access without replacing ``psycopg2``."""
    return psycopg2.connect(*args, **kwargs)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents (Public)"])

EMBEDDING_SERVICE_URL = _CONFIG_EMBEDDING_SERVICE_URL or "http://localhost:8001"
UPLOAD_STORAGE_BUCKET = os.getenv("UPLOADS_STORAGE_BUCKET") or os.getenv(
    "DOCUMENTS_UPLOADS_BUCKET", "documents"
)
UPLOADS_PUBLIC_BASE_URL = (
    os.getenv("UPLOADS_PUBLIC_BASE_URL") or os.getenv("DOCUMENTS_PUBLIC_BASE_URL") or ""
).rstrip("/")
EXCLUDED_TEST_TAGS = {"__e2e__", "__test__", "e2e", "test-data"}


def _build_public_storage_url(storage_bucket: str, storage_path: str) -> str | None:
    if not UPLOADS_PUBLIC_BASE_URL or not storage_bucket or not storage_path:
        return None
    encoded_path = quote(storage_path.lstrip("/"), safe="/")
    return f"{UPLOADS_PUBLIC_BASE_URL}/{storage_bucket}/{encoded_path}"


def _storage_path_from_source_url(source_url: str) -> str | None:
    if not source_url.startswith("upload://"):
        return None
    raw_path = source_url[len("upload://") :].strip()
    if not raw_path:
        return None
    return raw_path


def _extract_download_url(metadata: Any) -> str | None:
    if isinstance(metadata, str):
        metadata_text = metadata.strip()
        if metadata_text:
            try:
                metadata = json.loads(metadata_text)
            except Exception:
                metadata = {}
    if not isinstance(metadata, dict):
        return None
    download_url = metadata.get("download_url")
    if isinstance(download_url, str) and download_url.strip():
        return download_url.strip()
    return None


def _resolve_download_url(metadata: Any, source_url: str) -> str | None:
    explicit_download_url = _extract_download_url(metadata)
    if explicit_download_url:
        return explicit_download_url

    storage_path = _storage_path_from_source_url(source_url)
    if not storage_path:
        return None
    return _build_public_storage_url(UPLOAD_STORAGE_BUCKET, storage_path)


def _is_test_artifact(source_url: str, tags: list[str]) -> bool:
    normalized_tags = {str(tag).strip().lower() for tag in tags if str(tag).strip()}
    if normalized_tags.intersection(EXCLUDED_TEST_TAGS):
        return True
    if any(("e2e" in tag) or (tag in {"test", "testing"}) for tag in normalized_tags):
        return True

    source_lower = source_url.lower()
    if "e2e-" in source_lower or "?e2e=" in source_lower:
        return True

    return False


def _metadata_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc or ""
    except Exception:
        return ""


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _tag_label(tag: str, locale: str) -> str:
    normalized_locale = str(locale or "en").strip().lower()
    if normalized_locale.startswith("es"):
        translated = build_bilingual_tag_fields([tag]).get("tags_es", [])
        if translated:
            return translated[0]
    return tag


def _normalize_public_source(raw: dict[str, Any]) -> dict[str, Any]:
    url = str(raw.get("url") or raw.get("source_url") or "")
    metadata = _metadata_dict(raw.get("metadata"))
    domain = str(
        raw.get("domain")
        or raw.get("source_domain")
        or metadata.get("source_domain")
        or _domain_from_url(url)
    )
    total_chunks = _to_int(raw.get("total_chunks") or raw.get("chunk_count"), 0)

    tags = normalize_tags(raw.get("tags") or metadata.get("tags") or [])
    download_url = _resolve_download_url(metadata, url)
    language = str(
        raw.get("language")
        or metadata.get("language")
        or metadata.get("primary_language")
        or "Unknown"
    )
    primary_language_code = str(
        raw.get("primary_language_code") or metadata.get("primary_language_code") or "unknown"
    )
    available_languages = (
        raw.get("available_languages") or metadata.get("available_languages") or []
    )
    if not isinstance(available_languages, list):
        available_languages = [language] if language else []
    is_bilingual = bool(raw.get("is_bilingual") or metadata.get("is_bilingual"))

    return {
        "id": raw.get("id"),
        "url": url,
        "domain": domain,
        "source_domain": domain,
        "title": raw.get("title") or raw.get("document_title"),
        "description": raw.get("description"),
        "resource_type": raw.get("resource_type") or metadata.get("resource_type") or "document",
        "format": raw.get("format") or metadata.get("format") or "unknown",
        "author": raw.get("author"),
        "organization": raw.get("organization") or metadata.get("organization") or "unknown",
        "published_date": raw.get("published_date"),
        "first_scraped_at": raw.get("first_scraped_at") or raw.get("created_at"),
        "last_scraped_at": raw.get("last_scraped_at") or raw.get("updated_at"),
        "scrape_count": _to_int(raw.get("scrape_count"), 0),
        "is_active": bool(raw.get("is_active", True)),
        "reliability_score": raw.get("reliability_score"),
        "total_chunks": total_chunks,
        "total_characters": _to_int(raw.get("total_characters"), 0),
        "tags": tags,
        "metadata": metadata,
        "language": language,
        "primary_language": language,
        "primary_language_code": primary_language_code,
        "available_languages": available_languages,
        "is_bilingual": is_bilingual,
        "download_url": download_url,
        "downloadable": bool(download_url),
        "embedding_status": (
            raw.get("embedding_status") or metadata.get("embedding_status") or "completed"
        ),
        "source_of_truth": raw.get("source_of_truth")
        or metadata.get("source_of_truth")
        or "postgres",
        "canonical_visibility_updated_at": (
            raw.get("canonical_visibility_updated_at")
            or metadata.get("canonical_visibility_updated_at")
            or raw.get("updated_at")
            or raw.get("created_at")
        ),
    }


def _parse_query_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    parts = [part.strip() for part in str(tags).split(",") if part.strip()]
    return normalize_tags(parts)


def _tag_filter_match(source_tags: list[str], requested_tags: list[str], mode: str) -> bool:
    if not requested_tags:
        return True
    tag_set = set(normalize_tags(source_tags))
    if not tag_set:
        return False
    if mode == "all":
        return all(tag in tag_set for tag in requested_tags)
    return any(tag in tag_set for tag in requested_tags)


def _merge_sources_by_url(
    existing: list[dict[str, Any]],
    additional: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = list(existing)
    seen = {str(item.get("url") or "") for item in merged if item.get("url")}
    for item in additional:
        url = str(item.get("url") or "")
        if not url or url in seen:
            continue
        merged.append(item)
        seen.add(url)
    return merged


def _is_schema_profile_error(exc: Exception) -> bool:
    return "PGRST106" in str(exc)


def _is_data_backend_unavailable_error(exc: Exception) -> bool:
    if isinstance(exc, HTTPException):
        return exc.status_code == 503

    db_error_types = tuple(
        err_type
        for err_type in (
            getattr(psycopg2, "OperationalError", None),
            getattr(psycopg2, "InterfaceError", None),
            TimeoutError,
            ConnectionError,
        )
        if isinstance(err_type, type)
    )
    if db_error_types and isinstance(exc, db_error_types):
        return True

    message = str(exc).lower()
    patterns = (
        "could not connect to server",
        "connection refused",
        "connecterror",
        "timeout",
        "could not translate host name",
        "name or service not known",
        "temporary failure in name resolution",
        "could not resolve host",
        "server closed the connection unexpectedly",
        "connection not open",
        "database_url_not_configured",
        "database_url is not configured",
    )
    return any(pattern in message for pattern in patterns)


def _set_statement_timeout(cur: Any, timeout_ms: int = 30000) -> None:
    safe_timeout_ms = max(int(timeout_ms), 1000)
    cur.execute(f"SET statement_timeout = {safe_timeout_ms}")


def _raise_documents_error(endpoint_name: str, exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc

    if _is_data_backend_unavailable_error(exc) or should_fail_closed_for_projection_error(exc):
        logger.warning("%s degraded: Postgres unavailable (%s)", endpoint_name, exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Document index is temporarily unavailable because the database is not reachable. "
                "Please retry shortly."
            ),
        ) from exc
    logger.exception("%s error", endpoint_name)
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def _load_overview_via_sql() -> tuple[dict[str, int], list[dict[str, Any]]]:
    database_url = get_resolved_database_url()
    if not database_url:
        raise RuntimeError("database_url_not_configured")

    with _pg_connect(database_url, connect_timeout=5) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _set_statement_timeout(cur)
            cur.execute("""
                SELECT
                    COUNT(*)::int AS total_chunks,
                    COALESCE(AVG(COALESCE(chunk_size, LENGTH(content)))::int, 0) AS avg_chunk_size
                FROM public.document_chunks
                """)
            stats_row: dict[str, Any] = cur.fetchone() or {}

            cur.execute("""
                SELECT
                    id,
                    url,
                    domain,
                    title,
                    description,
                    author,
                    published_date,
                    first_scraped_at,
                    last_scraped_at,
                    scrape_count,
                    is_active,
                    reliability_score,
                    total_chunks,
                    total_characters,
                    metadata,
                    created_at,
                    updated_at
                FROM public.sources
                ORDER BY COALESCE(total_chunks, 0) DESC, COALESCE(last_scraped_at, created_at) DESC
                LIMIT 2000
                """)
            source_rows = [dict(row) for row in (cur.fetchall() or [])]

            cur.execute("""
                SELECT
                    source_url AS url,
                    MAX(source_domain) AS source_domain,
                    MAX(document_title) AS title,
                    COUNT(*)::int AS total_chunks,
                    MAX(NULLIF(metadata->>'language', '')) AS language,
                    MAX(NULLIF(metadata->>'primary_language_code', '')) AS primary_language_code,
                    COALESCE(
                        ARRAY_REMOVE(ARRAY_AGG(DISTINCT NULLIF(metadata->>'language', '')), NULL),
                        ARRAY[]::text[]
                    ) AS available_languages,
                    BOOL_OR(COALESCE((metadata->>'is_bilingual')::boolean, FALSE)) AS is_bilingual,
                    MIN(created_at) AS created_at,
                    MAX(updated_at) AS updated_at
                FROM public.document_chunks
                WHERE source_url IS NOT NULL AND source_url <> ''
                GROUP BY source_url
                ORDER BY COUNT(*) DESC
                LIMIT 5000
                """)
            chunk_rows = [dict(row) for row in (cur.fetchall() or [])]

    normalized_sources = [_normalize_public_source(row) for row in source_rows]
    normalized_chunks = [_normalize_public_source(row) for row in chunk_rows]
    merged = _merge_sources_by_url(normalized_sources, normalized_chunks)
    merged = sorted(merged, key=lambda item: _to_int(item.get("total_chunks"), 0), reverse=True)

    stats = {
        "total_chunks": _to_int(stats_row.get("total_chunks"), 0),
        "avg_chunk_size": _to_int(stats_row.get("avg_chunk_size"), 0),
    }
    return stats, merged


def _load_chunk_statistics_via_sql(limit: int) -> list[dict[str, Any]]:
    database_url = get_resolved_database_url()
    if not database_url:
        raise RuntimeError("database_url_not_configured")

    with _pg_connect(database_url, connect_timeout=5) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _set_statement_timeout(cur)
            cur.execute(
                """
                SELECT
                    COALESCE(
                        NULLIF(source_domain, ''),
                        split_part(regexp_replace(COALESCE(source_url, ''), '^https?://', ''), '/', 1),
                        'unknown'
                    ) AS source_domain,
                    COUNT(*)::int AS chunk_count,
                    COALESCE(AVG(COALESCE(chunk_size, LENGTH(content)))::int, 0) AS avg_chunk_size,
                    COALESCE(SUM(COALESCE(chunk_size, LENGTH(content)))::bigint, 0) AS total_size,
                    COUNT(DISTINCT COALESCE(NULLIF(source_url, ''), source_domain))::int AS document_count,
                    MAX(COALESCE(updated_at, created_at)) AS latest_chunk
                FROM public.document_chunks
                GROUP BY 1
                ORDER BY COUNT(*) DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(row) for row in (cur.fetchall() or [])]


# ---------------------------------------------------------------------------
# Overview endpoint
# ---------------------------------------------------------------------------


@router.get("/overview", response_model=DocumentsOverviewResponse)
async def documents_overview(
    params: Annotated[DocumentsOverviewQueryParams, Depends()],
) -> DocumentsOverviewResponse:
    """
    Return corpus-level statistics for the public Documents Dashboard.

    Fields:
    - total_chunks: total rows in document_chunks
    - unique_sources: count of distinct source_url values
    - avg_chunk_size: average character length of content column
    - embedding_model: active model name from embedding_metadata (or env fallback)
    - embedding_dimension: vector dimension
    - sources: list of {url, title, domain, total_chunks, is_active}
    """
    try:
        stats, source_rows = _load_overview_via_sql()
        if not params.include_test_data:
            source_rows = [
                item
                for item in source_rows
                if not _is_test_artifact(item.get("url") or "", item.get("tags") or [])
            ]
        requested_tags = _parse_query_tags(params.tags)
        if requested_tags:
            source_rows = [
                item
                for item in source_rows
                if _tag_filter_match(item.get("tags") or [], requested_tags, params.tag_match_mode)
            ]
        source_rows.sort(key=lambda item: _to_int(item.get("total_chunks"), 0), reverse=True)

        sources = [PublicDocumentsSourceItem.model_validate(item) for item in source_rows]
        return DocumentsOverviewResponse(
            total_chunks=_to_int(stats.get("total_chunks"), 0),
            unique_sources=len(source_rows),
            filtered=bool(requested_tags),
            avg_chunk_size=_to_int(stats.get("avg_chunk_size"), 0),
            embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "384")),
            sources=sources,
        )

    except Exception as exc:
        _raise_documents_error("documents_overview", exc)


# ---------------------------------------------------------------------------
# Preview endpoint
# ---------------------------------------------------------------------------


@router.get("/preview", response_model=DocumentsPreviewResponse)
async def documents_preview(
    params: Annotated[DocumentsPreviewQueryParams, Depends()],
) -> DocumentsPreviewResponse:
    """
    Return the first N chunk excerpts for a given source URL.
    Used by the Documents Dashboard source-preview drawer.
    """
    try:
        database_url = get_resolved_database_url()
        if not database_url:
            raise RuntimeError("database_url_not_configured")

        chunks = []
        with _pg_connect(database_url, connect_timeout=5) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                _set_statement_timeout(cur)
                cur.execute(
                    """
                    SELECT chunk_index, chunk_size, content, metadata
                    FROM public.document_chunks
                    WHERE source_url = %s
                    ORDER BY chunk_index ASC NULLS LAST, created_at ASC
                    LIMIT %s
                    """,
                    (params.source_url, max(params.limit, 1)),
                )
                rows = cur.fetchall() or []

        for idx, row in enumerate(rows):
            metadata = _metadata_dict(row.get("metadata"))
            content = str(row.get("content") or "")
            chunks.append(
                {
                    "chunk_index": _to_int(row.get("chunk_index"), idx),
                    "chunk_size": _to_int(row.get("chunk_size"), len(content)),
                    "content_preview": content[:400],
                    "document_title": metadata.get("document_title") or params.source_url,
                }
            )

        if not chunks:
            raise HTTPException(status_code=404, detail="Source not found")

        chunks.sort(key=lambda item: _to_int(item.get("chunk_index"), 0))
        chunks = chunks[: params.limit]
        preview_chunks = [DocumentsPreviewChunk.model_validate(c) for c in chunks]
        return DocumentsPreviewResponse(source_url=params.source_url, chunks=preview_chunks)
    except Exception as exc:
        _raise_documents_error("documents_preview", exc)


@router.get("/download-url", response_model=DocumentsDownloadUrlResponse)
async def documents_download_url(
    params: Annotated[DocumentsDownloadUrlQueryParams, Depends()],
) -> DocumentsDownloadUrlResponse:
    """Resolve a download URL for a source when available.

    For URL-only sources (no downloadable artifact), returns 200 with
    downloadable=false so clients can avoid raising user-visible errors.
    """
    try:
        database_url = get_resolved_database_url()
        if not database_url:
            raise RuntimeError("database_url_not_configured")

        source_row: dict[str, Any] | None = None
        chunk_row: dict[str, Any] | None = None

        with _pg_connect(database_url, connect_timeout=5) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                _set_statement_timeout(cur)
                cur.execute(
                    """
                    SELECT url, title, metadata
                    FROM public.sources
                    WHERE url = %s
                    LIMIT 1
                    """,
                    (params.source_url,),
                )
                source_row = cast(dict[str, Any] | None, cur.fetchone())

                if source_row is None:
                    cur.execute(
                        """
                        SELECT metadata
                        FROM public.document_chunks
                        WHERE source_url = %s
                        LIMIT 1
                        """,
                        (params.source_url,),
                    )
                    chunk_row = cast(dict[str, Any] | None, cur.fetchone())

        if source_row:
            metadata = source_row.get("metadata") or {}
            download_url = _resolve_download_url(metadata, params.source_url)
            if download_url:
                return DocumentsDownloadUrlResponse(
                    source_url=params.source_url,
                    title=str(source_row.get("title") or params.source_url),
                    download_url=download_url,
                    downloadable=True,
                )
            return DocumentsDownloadUrlResponse(
                source_url=params.source_url,
                title=str(source_row.get("title") or params.source_url),
                download_url=None,
                downloadable=False,
                message="Source is URL-based and has no downloadable file",
            )

        if not chunk_row:
            raise HTTPException(status_code=404, detail="Source not found")

        metadata = _metadata_dict(chunk_row.get("metadata"))
        download_url = _resolve_download_url(metadata, params.source_url)
        if not download_url:
            return DocumentsDownloadUrlResponse(
                source_url=params.source_url,
                title=str(metadata.get("document_title") or params.source_url),
                download_url=None,
                downloadable=False,
                message="Source is URL-based and has no downloadable file",
            )

        return DocumentsDownloadUrlResponse(
            source_url=params.source_url,
            title=str(metadata.get("document_title") or params.source_url),
            download_url=download_url,
            downloadable=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_documents_error("documents_download_url", exc)


@router.get("/chunk-statistics", response_model=DocumentsChunkStatisticsResponse)
async def documents_chunk_statistics(
    params: Annotated[DocumentsChunkStatisticsQueryParams, Depends()],
) -> DocumentsChunkStatisticsResponse:
    """Return per-domain chunk statistics from Postgres metadata."""
    try:
        rows = _load_chunk_statistics_via_sql(params.limit)
        rows = rows[: params.limit]
        typed = [DocumentsChunkStatisticsRow.model_validate(r) for r in rows]
        return DocumentsChunkStatisticsResponse(rows=typed, total=len(typed))
    except Exception as exc:
        _raise_documents_error("documents_chunk_statistics", exc)


@router.get("/tags", response_model=DocumentsTagsResponse)
async def documents_tags(
    params: Annotated[DocumentsTagsQueryParams, Depends()],
) -> DocumentsTagsResponse:
    """Return tag inventory and counts for Documents filtering UI."""
    try:
        database_url = get_resolved_database_url()
        if not database_url:
            raise RuntimeError("database_url_not_configured")

        normalized_query = (params.query or "").strip().lower()

        chunk_counts: dict[str, int] = {}
        source_map: dict[str, set[str]] = {}
        with _pg_connect(database_url, connect_timeout=5) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                _set_statement_timeout(cur)
                cur.execute("SELECT source_url, metadata FROM public.document_chunks")
                rows = cur.fetchall() or []

        for row in rows:
            metadata = _metadata_dict(row.get("metadata"))
            source_url = str(metadata.get("source_url") or "")
            tags = normalize_tags(
                metadata.get("tags") or metadata.get("tags_en") or metadata.get("tags_es") or []
            )
            if not params.include_test_data and _is_test_artifact(source_url, tags):
                continue
            for tag in tags:
                chunk_counts[tag] = chunk_counts.get(tag, 0) + 1
                if source_url:
                    source_map.setdefault(tag, set()).add(source_url)

        response_rows: list[dict[str, Any]] = []
        tag_counts: dict[str, int] = {}
        for tag, chunk_count in chunk_counts.items():
            label = _tag_label(tag, params.locale)
            if normalized_query and normalized_query not in tag and normalized_query not in label:
                continue
            resource_count = len(source_map.get(tag, set()))
            tag_counts[tag] = resource_count
            response_rows.append(
                {
                    "tag": tag,
                    "label": label,
                    "locale": params.locale,
                    "resource_count": resource_count,
                    "chunk_count": chunk_count,
                    "source_count": resource_count,
                }
            )

        response_rows.sort(
            key=lambda item: (
                _to_int(item.get("resource_count"), 0),
                _to_int(item.get("source_count"), 0),
                _to_int(item.get("chunk_count"), 0),
                str(item.get("tag", "")),
            ),
            reverse=True,
        )
        response_rows = response_rows[: params.limit]

        tag_models = [DocumentsTagRow.model_validate(item) for item in response_rows]
        return DocumentsTagsResponse(
            tags=tag_models,
            tag_counts=tag_counts,
            locale=params.locale,
            total=len(tag_models),
        )
    except Exception as exc:
        _raise_documents_error("documents_tags", exc)
