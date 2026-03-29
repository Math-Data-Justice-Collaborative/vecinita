"""
Public Documents Router

Read-only, unauthenticated endpoints that power the public Documents Dashboard.
Exposes corpus metadata: embedding model, chunk stats, source list, and chunk previews.
No auth required — all data is non-sensitive metadata about the public knowledge base.
"""

import json
import logging
import os
from typing import Any
from urllib.parse import urlparse

import psycopg2  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor  # type: ignore[import-untyped]
from supabase import Client, create_client

from src.services.chroma_store import get_chroma_store
from src.utils.tags import normalize_tags

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents (Public)"])

EMBEDDING_SERVICE_URL = (
    os.getenv("MODAL_EMBEDDING_ENDPOINT")
    or os.getenv("EMBEDDING_SERVICE_URL")
    or "http://vecinita-modal-proxy-v1:10000/embedding"
)
UPLOAD_STORAGE_BUCKET = os.getenv("SUPABASE_UPLOADS_BUCKET", "documents")
EXCLUDED_TEST_TAGS = {"__e2e__", "__test__", "e2e", "test-data"}


def _get_db() -> Client | None:
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )
    if not url or not key:
        logger.warning("Documents API running without database configuration.")
        return None
    try:
        return create_client(url, key)
    except Exception as exc:
        logger.warning("Failed to initialize database client for documents API: %s", exc)
        return None


def _build_public_storage_url(storage_bucket: str, storage_path: str) -> str | None:
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not supabase_url or not storage_bucket or not storage_path:
        return None
    return f"{supabase_url}/storage/v1/object/public/{storage_bucket}/{storage_path}"


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
    return _extract_download_url(metadata)


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

    return {
        "id": raw.get("id"),
        "url": url,
        "domain": domain,
        "source_domain": domain,
        "title": raw.get("title") or raw.get("document_title"),
        "description": raw.get("description"),
        "author": raw.get("author"),
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
        "download_url": download_url,
        "downloadable": bool(download_url),
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


def _is_chroma_unavailable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "could not connect to a chroma server" in message
        or "connection refused" in message
        or "connecterror" in message
    )


def _raise_documents_error(endpoint_name: str, exc: Exception) -> None:
    if _is_chroma_unavailable_error(exc):
        logger.warning("%s degraded: Chroma unavailable (%s)", endpoint_name, exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Document index is temporarily unavailable because Chroma is not reachable. "
                "Please retry shortly."
            ),
        ) from exc
    logger.exception("%s error", endpoint_name)
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def _load_overview_via_sql() -> tuple[dict[str, int], list[dict[str, Any]]]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"total_chunks": 0, "avg_chunk_size": 0}, []

    with psycopg2.connect(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return []

    with psycopg2.connect(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
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


@router.get("/overview")
async def documents_overview(
    tags: str | None = Query(None, description="Comma-separated tags used to filter source list"),
    tag_match_mode: str = Query(
        "any", pattern="^(any|all)$", description="Tag match mode for source filtering"
    ),
    include_test_data: bool = Query(
        False, description="Include test/e2e-tagged artifacts in results"
    ),
    db: Client | None = Depends(_get_db),
) -> dict[str, Any]:
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
        store = get_chroma_store()
        all_chunks = list(store.iter_all_chunks())

        total_chunks = len(all_chunks)
        total_size = 0
        source_index: dict[str, dict[str, Any]] = {}

        for row in all_chunks:
            metadata = _metadata_dict(row.get("metadata"))
            content = str(row.get("content") or "")
            chunk_size = _to_int(metadata.get("chunk_size"), len(content))
            total_size += chunk_size
            chunk_tags = normalize_tags(metadata.get("tags") or [])
            chunk_download_url = _extract_download_url(metadata)

            source_url = str(metadata.get("source_url") or "")
            if not source_url:
                continue

            current = source_index.get(source_url)
            if current is None:
                current = {
                    "url": source_url,
                    "source_domain": metadata.get("source_domain") or _domain_from_url(source_url),
                    "title": metadata.get("document_title") or source_url,
                    "total_chunks": 0,
                    "metadata": metadata,
                    "is_active": True,
                    "tags": [],
                    "download_url": chunk_download_url,
                }
                source_index[source_url] = current
            current["total_chunks"] = _to_int(current.get("total_chunks"), 0) + 1
            merged_tags = normalize_tags((current.get("tags") or []) + chunk_tags)
            current["tags"] = merged_tags
            if not current.get("download_url") and chunk_download_url:
                current["download_url"] = chunk_download_url

        source_rows = [_normalize_public_source(item) for item in source_index.values()]
        if not include_test_data:
            source_rows = [
                item
                for item in source_rows
                if not _is_test_artifact(item.get("url") or "", item.get("tags") or [])
            ]
        requested_tags = _parse_query_tags(tags)
        if requested_tags:
            source_rows = [
                item
                for item in source_rows
                if _tag_filter_match(item.get("tags") or [], requested_tags, tag_match_mode)
            ]
        source_rows.sort(key=lambda item: _to_int(item.get("total_chunks"), 0), reverse=True)

        avg_chunk_size = int(total_size / total_chunks) if total_chunks else 0

        return {
            "total_chunks": total_chunks,
            "unique_sources": len(source_rows),
            "filtered": bool(requested_tags),
            "avg_chunk_size": avg_chunk_size,
            "embedding_model": os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            "embedding_dimension": int(os.getenv("EMBEDDING_DIMENSION", "384")),
            "sources": source_rows,
        }

    except Exception as exc:
        _raise_documents_error("documents_overview", exc)


# ---------------------------------------------------------------------------
# Preview endpoint
# ---------------------------------------------------------------------------


@router.get("/preview")
async def documents_preview(
    source_url: str = Query(..., description="Source URL to preview"),
    limit: int = Query(3, ge=1, le=10, description="Number of chunks to return"),
    db: Client | None = Depends(_get_db),
) -> dict[str, Any]:
    """
    Return the first N chunk excerpts for a given source URL.
    Used by the Documents Dashboard source-preview drawer.
    """
    try:
        store = get_chroma_store()
        res = store.get_chunks(where={"source_url": source_url}, limit=max(limit, 1), offset=0)
        chunks = []
        ids = res.get("ids") or []
        docs = res.get("documents") or []
        metas = res.get("metadatas") or []
        for idx in range(len(ids)):
            metadata = _metadata_dict(metas[idx] if idx < len(metas) else {})
            content = str(docs[idx] if idx < len(docs) and docs[idx] is not None else "")
            chunks.append(
                {
                    "chunk_index": _to_int(metadata.get("chunk_index"), idx),
                    "chunk_size": _to_int(metadata.get("chunk_size"), len(content)),
                    "content_preview": content[:400],
                    "document_title": metadata.get("document_title") or source_url,
                }
            )
        chunks.sort(key=lambda item: _to_int(item.get("chunk_index"), 0))
        chunks = chunks[:limit]
        return {"source_url": source_url, "chunks": chunks}
    except Exception as exc:
        _raise_documents_error("documents_preview", exc)


@router.get("/download-url")
async def documents_download_url(
    source_url: str = Query(..., description="Source URL to resolve download link"),
    db: Client | None = Depends(_get_db),
) -> dict[str, Any]:
    """Resolve a download URL for a source when available.

    For URL-only sources (no downloadable artifact), returns 200 with
    downloadable=false so clients can avoid raising user-visible errors.
    """
    try:
        store = get_chroma_store()
        source_entry = store.get_source(source_url)
        source_row = source_entry if source_entry else None

        if source_row:
            metadata = source_row.get("metadata") or {}
            download_url = _resolve_download_url(metadata, source_url)
            if download_url:
                return {
                    "source_url": source_url,
                    "title": source_row.get("title") or source_url,
                    "download_url": download_url,
                    "downloadable": True,
                }
            return {
                "source_url": source_url,
                "title": source_row.get("title") or source_url,
                "download_url": None,
                "downloadable": False,
                "message": "Source is URL-based and has no downloadable file",
            }

        chunk_result = store.get_chunks(where={"source_url": source_url}, limit=1, offset=0)
        ids = chunk_result.get("ids") or []
        metas = chunk_result.get("metadatas") or []
        if not ids:
            raise HTTPException(status_code=404, detail="Source not found")

        metadata = _metadata_dict(metas[0] if metas else {})
        download_url = _resolve_download_url(metadata, source_url)
        if not download_url:
            return {
                "source_url": source_url,
                "title": metadata.get("document_title") or source_url,
                "download_url": None,
                "downloadable": False,
                "message": "Source is URL-based and has no downloadable file",
            }

        return {
            "source_url": source_url,
            "title": metadata.get("document_title") or source_url,
            "download_url": download_url,
            "downloadable": True,
        }
    except HTTPException:
        raise
    except Exception as exc:
        _raise_documents_error("documents_download_url", exc)


@router.get("/chunk-statistics")
async def documents_chunk_statistics(
    limit: int = Query(20, ge=1, le=200, description="Maximum domains to return"),
    db: Client | None = Depends(_get_db),
) -> dict[str, Any]:
    """Return per-domain chunk statistics from Chroma metadata."""
    try:
        store = get_chroma_store()
        buckets: dict[str, dict[str, Any]] = {}

        for row in store.iter_all_chunks():
            metadata = _metadata_dict(row.get("metadata"))
            source_domain = str(metadata.get("source_domain") or "unknown")
            source_url = str(metadata.get("source_url") or "")
            content = str(row.get("content") or "")
            chunk_size = _to_int(metadata.get("chunk_size"), len(content))
            latest_chunk = metadata.get("updated_at") or metadata.get("created_at")

            current = buckets.get(source_domain)
            if current is None:
                current = {
                    "source_domain": source_domain,
                    "chunk_count": 0,
                    "avg_chunk_size": 0,
                    "total_size": 0,
                    "document_count": 0,
                    "latest_chunk": latest_chunk,
                    "_sources": set(),
                }
                buckets[source_domain] = current

            current["chunk_count"] += 1
            current["total_size"] += chunk_size
            if source_url:
                current["_sources"].add(source_url)
            if latest_chunk and (
                not current.get("latest_chunk") or str(latest_chunk) > str(current["latest_chunk"])
            ):
                current["latest_chunk"] = latest_chunk

        rows: list[dict[str, Any]] = []
        for item in buckets.values():
            chunk_count = _to_int(item.get("chunk_count"), 0)
            item["avg_chunk_size"] = int(item["total_size"] / chunk_count) if chunk_count else 0
            item["document_count"] = len(item.pop("_sources", set()))
            rows.append(item)

        rows.sort(key=lambda r: _to_int(r.get("chunk_count"), 0), reverse=True)
        rows = rows[:limit]
        return {"rows": rows, "total": len(rows)}
    except Exception as exc:
        _raise_documents_error("documents_chunk_statistics", exc)


@router.get("/tags")
async def documents_tags(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of tags to return"),
    query: str = Query("", description="Optional case-insensitive tag search"),
    include_test_data: bool = Query(False, description="Include tags from test/e2e artifacts"),
    db: Client | None = Depends(_get_db),
) -> dict[str, Any]:
    """Return tag inventory and counts for Documents filtering UI."""
    try:
        store = get_chroma_store()
        normalized_query = (query or "").strip().lower()

        chunk_counts: dict[str, int] = {}
        source_map: dict[str, set[str]] = {}
        for row in store.iter_all_chunks():
            metadata = _metadata_dict(row.get("metadata"))
            source_url = str(metadata.get("source_url") or "")
            tags = normalize_tags(metadata.get("tags") or [])
            if not include_test_data and _is_test_artifact(source_url, tags):
                continue
            for tag in tags:
                chunk_counts[tag] = chunk_counts.get(tag, 0) + 1
                if source_url:
                    source_map.setdefault(tag, set()).add(source_url)

        rows = []
        for tag, chunk_count in chunk_counts.items():
            if normalized_query and normalized_query not in tag:
                continue
            rows.append(
                {
                    "tag": tag,
                    "chunk_count": chunk_count,
                    "source_count": len(source_map.get(tag, set())),
                }
            )

        rows.sort(
            key=lambda item: (
                _to_int(item.get("source_count"), 0),
                _to_int(item.get("chunk_count"), 0),
                str(item.get("tag", "")),
            ),
            reverse=True,
        )
        rows = rows[:limit]

        return {"tags": rows, "total": len(rows)}
    except Exception as exc:
        _raise_documents_error("documents_tags", exc)
