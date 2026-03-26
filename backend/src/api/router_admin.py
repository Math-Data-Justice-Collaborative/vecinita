"""
Unified API Gateway - Admin Router

Endpoints for database management, statistics, and system administration.
Write endpoints (upload, source management) require Supabase JWT auth
with role=admin in app_metadata.
"""

import asyncio
import hashlib
import io
import json
import logging
import os
import secrets
import tempfile
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, cast
from urllib.parse import urlparse

import httpx
import psycopg2  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg2.extras import RealDictCursor  # type: ignore[import-untyped]
from pydantic import BaseModel, Field
from supabase import Client, create_client

from src.services.chroma_store import get_chroma_store
from src.utils.tags import normalize_tags, parse_tags_input

from ..services.db.schema_diagnostics import get_validation_summary, validate_schema
from ..services.scraper.scraper import VecinaScraper
from .models import (
    AdminHealthResponse,
    AdminStatsResponse,
    CleanDatabaseRequest,
    CleanDatabaseResponse,
    CleanRequestTokenResponse,
    DatabaseStats,
    DeleteChunkResponse,
    DocumentChunk,
    DocumentsListResponse,
    SourcesListResponse,
    ValidateSourceRequest,
    ValidateSourceResponse,
)

router = APIRouter(prefix="/admin", tags=["Administration"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

# Configuration - will be set by main.py
ADMIN_CONFIG = {
    "require_confirmation": True,
    "delete_chunk_batch_size": 1000,
}

# Service URLs from environment
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
EMBEDDING_SERVICE_AUTH_TOKEN = os.getenv("EMBEDDING_SERVICE_AUTH_TOKEN") or os.getenv(
    "MODAL_API_PROXY_SECRET"
)
UPLOAD_STORAGE_BUCKET = os.getenv("SUPABASE_UPLOADS_BUCKET", "documents")

# Token storage (in-memory for now, use Redis for production)
_cleanup_tokens: dict[str, datetime] = {}


def _embedding_service_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if EMBEDDING_SERVICE_AUTH_TOKEN:
        headers["x-embedding-service-token"] = EMBEDDING_SERVICE_AUTH_TOKEN
    return headers


def _parse_queue_file_path(file_path: str) -> dict[str, Any]:
    """Parse queue file_path for hybrid URL/file job support.

    URL jobs are encoded as: url::<depth>::<url>
    """
    if not file_path:
        return {"type": "file", "url": None, "depth": 1, "file_path": ""}

    if file_path.startswith("url::"):
        remainder = file_path[len("url::") :]
        depth = 1
        url = remainder
        if "::" in remainder:
            depth_text, parsed_url = remainder.split("::", 1)
            try:
                depth = int(depth_text)
            except ValueError:
                depth = 1
            url = parsed_url
        return {
            "type": "url",
            "url": url,
            "depth": depth,
            "file_path": file_path,
        }

    return {"type": "file", "url": None, "depth": 1, "file_path": file_path}


class SourceTagsUpdateRequest(BaseModel):
    """Request body for editing source-level metadata tags."""

    url: str
    tags: list[str]


class BatchSourceIngestRequest(BaseModel):
    """Request body for bulk source ingestion from pasted urls.txt content."""

    urls_text: str | None = None
    urls: list[str] = Field(default_factory=list)
    depth: int = 1
    tags: list[str] = Field(default_factory=list)
    tag_mode: Literal["none", "baseline_only", "auto_infer"] = "auto_infer"


def _extract_tags(metadata: Any) -> list[str]:
    if isinstance(metadata, str):
        metadata_text = metadata.strip()
        if metadata_text:
            try:
                metadata = json.loads(metadata_text)
            except Exception:
                metadata = {}
    if not isinstance(metadata, dict):
        return []
    tags = metadata.get("tags")
    if isinstance(tags, list):
        return normalize_tags(tags)
    return []


def _safe_metadata_dict(metadata: Any) -> dict[str, Any]:
    if isinstance(metadata, dict):
        return metadata
    if isinstance(metadata, str):
        text = metadata.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _normalize_lang(lang: str | None) -> str:
    value = (lang or "").strip().lower()
    return "es" if value.startswith("es") else "en"


def _tagging_message(message_key: str, lang: str) -> str:
    messages = {
        "tags_updated": {
            "en": "Source tags updated successfully.",
            "es": "Las etiquetas de la fuente se actualizaron correctamente.",
        },
        "tags_update_failed": {
            "en": "Failed to propagate tags to chunks",
            "es": "No se pudieron propagar las etiquetas a los fragmentos",
        },
        "tags_fetch_failed": {
            "en": "Failed to fetch metadata tags",
            "es": "No se pudieron obtener las etiquetas de metadatos",
        },
    }
    normalized_lang = _normalize_lang(lang)
    return messages.get(message_key, {}).get(normalized_lang, message_key)


def _domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc or ""
    except Exception:
        return ""


def _parse_urls_text(urls_text: str | None, urls: list[str] | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    for value in urls or []:
        normalized = (value or "").strip()
        if not normalized or normalized.startswith("#"):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)

    for raw_line in (urls_text or "").splitlines():
        normalized = raw_line.strip()
        if not normalized or normalized.startswith("#"):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)

    return ordered


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _normalize_source_row(raw: dict[str, Any], *, fallback_total_chunks: int = 0) -> dict[str, Any]:
    url = str(raw.get("url") or raw.get("source_url") or "")
    metadata = _safe_metadata_dict(raw.get("metadata"))
    domain = str(
        raw.get("domain")
        or raw.get("source_domain")
        or metadata.get("source_domain")
        or _domain_from_url(url)
    )
    total_chunks = _to_int(raw.get("total_chunks") or raw.get("chunk_count"), fallback_total_chunks)

    normalized = {
        "id": raw.get("id"),
        "url": url,
        "domain": domain,
        "source_domain": domain,
        "title": raw.get("title"),
        "description": raw.get("description"),
        "author": raw.get("author"),
        "published_date": raw.get("published_date"),
        "first_scraped_at": raw.get("first_scraped_at") or raw.get("created_at"),
        "last_scraped_at": raw.get("last_scraped_at")
        or raw.get("last_updated")
        or raw.get("updated_at"),
        "scrape_count": _to_int(raw.get("scrape_count"), 0),
        "is_active": bool(raw.get("is_active", True)),
        "reliability_score": raw.get("reliability_score"),
        "total_chunks": total_chunks,
        "chunk_count": total_chunks,
        "total_characters": _to_int(raw.get("total_characters"), 0),
        "metadata": metadata,
        "tags": _extract_tags(metadata),
        "created_at": raw.get("created_at"),
        "updated_at": raw.get("updated_at") or raw.get("last_updated"),
    }
    return normalized


def _list_sources_via_sql(limit: int = 1000) -> list[dict[str, Any]]:
    """Fallback source aggregation via direct PostgreSQL connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured for SQL fallback")

    query = """
    SELECT
      source_url AS url,
      COUNT(*)::int AS chunk_count,
      COUNT(*)::int AS total_chunks,
      MIN(created_at) AS created_at,
      MAX(updated_at) AS last_updated
    FROM public.document_chunks
    GROUP BY source_url
    ORDER BY chunk_count DESC
    LIMIT %s
    """

    with psycopg2.connect(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall() or []

    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = _normalize_source_row(dict(row))
        normalized.append(item)
    return normalized


def get_database_client() -> Client:
    """
    Dependency to get Supabase database client.

    Returns:
        Supabase client instance

    Raises:
        HTTPException: If database credentials not configured
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Database not configured. Set SUPABASE_URL and a Supabase key (SUPABASE_SECRET_KEY or SUPABASE_KEY).",
        )

    return create_client(supabase_url, supabase_key)


def _verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify Bearer token is a valid Supabase session with role=admin."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header required.")
    token = credentials.credentials

    dev_admin_enabled = os.getenv("DEV_ADMIN_ENABLED", "false").lower() in ["true", "1", "yes"]
    dev_admin_bearer_token = os.getenv("DEV_ADMIN_BEARER_TOKEN", "")

    if dev_admin_enabled and dev_admin_bearer_token:
        if secrets.compare_digest(token, dev_admin_bearer_token):
            return {
                "id": "dev-admin-local",
                "email": "dev-admin@local",
                "app_metadata": {"role": "admin"},
            }

    db = get_database_client()
    try:
        user_resp = db.auth.get_user(token)
        user = user_resp.user if hasattr(user_resp, "user") else user_resp  # type: ignore[union-attr]
        app_meta = getattr(user, "app_metadata", {}) or {}
        if app_meta.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin role required.")
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}")


@router.get("/health")
async def admin_health_check(
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
) -> AdminHealthResponse:
    """
    Check health of all backend services.

    Particularly useful for debugging deployment issues.

    Returns:
        Health status of agent, embedding service, database
    """
    # Check agent service
    agent_health: dict[str, Any] = {"status": "error"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.time()
            response = await client.get(f"{AGENT_SERVICE_URL}/health")
            elapsed_ms = int((time.time() - start) * 1000)
            if response.status_code == 200:
                agent_health = {
                    "status": "ok",
                    "response_time_ms": elapsed_ms,
                    "last_check": datetime.now(timezone.utc).isoformat(),
                }
            else:
                agent_health = {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "last_check": datetime.now(timezone.utc).isoformat(),
                }
    except Exception as e:
        agent_health = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }

    # Check embedding service
    embedding_health: dict[str, Any] = {"status": "error"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.time()
            response = await client.get(f"{EMBEDDING_SERVICE_URL}/health")
            elapsed_ms = int((time.time() - start) * 1000)
            if response.status_code == 200:
                embedding_health = {
                    "status": "ok",
                    "response_time_ms": elapsed_ms,
                    "last_check": datetime.now(timezone.utc).isoformat(),
                }
            else:
                embedding_health = {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "last_check": datetime.now(timezone.utc).isoformat(),
                }
    except Exception as e:
        embedding_health = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }

    # Check database
    db_health: dict[str, Any] = {"status": "error"}
    chroma_status: dict[str, Any] = {"status": "error"}
    try:
        store = get_chroma_store()
        chroma_ok = store.heartbeat()
        chroma_status = {
            "status": "ok" if chroma_ok else "error",
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        chroma_status = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
        }

    try:
        # Simple query to test connection
        db.table("document_chunks").select(
            "id",
            count="exact",  # type: ignore[arg-type]
        ).limit(1).execute()
        db_health = {
            "status": "ok",
            "last_check": datetime.now(timezone.utc).isoformat(),
            "vector_store": {
                "primary": "chroma",
                "sync_mode": "dual_write_degraded",
                "chroma": chroma_status,
                "supabase_fallback_reads_enabled": os.getenv(
                    "VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true"
                ).lower()
                in ["1", "true", "yes"],
                "supabase_dual_write_enabled": os.getenv("VECTOR_SYNC_ENABLED", "true").lower()
                in ["1", "true", "yes"],
            },
        }
    except Exception as e:
        db_health = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.now(timezone.utc).isoformat(),
            "vector_store": {
                "primary": "chroma",
                "sync_mode": "dual_write_degraded",
                "chroma": chroma_status,
                "supabase_fallback_reads_enabled": os.getenv(
                    "VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true"
                ).lower()
                in ["1", "true", "yes"],
                "supabase_dual_write_enabled": os.getenv("VECTOR_SYNC_ENABLED", "true").lower()
                in ["1", "true", "yes"],
            },
        }

    # Determine overall status
    all_healthy = (
        agent_health["status"] == "ok"
        and embedding_health["status"] == "ok"
        and db_health["status"] == "ok"
    )
    overall_status = "healthy" if all_healthy else "degraded"

    return AdminHealthResponse(
        status=overall_status,
        agent_service=agent_health,
        embedding_service=embedding_health,
        database=db_health,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/stats")
async def get_database_stats(
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
) -> AdminStatsResponse:
    """
    Get comprehensive database and system statistics.

    Returns:
        - Database: chunk count, unique sources, embeddings status
        - Services: availability, configuration
    """
    try:
        # Get total chunks
        total_result = (
            db.table("document_chunks")
            .select(
                "*",
                count="exact",  # type: ignore[arg-type]
            )
            .limit(1)
            .execute()
        )
        total_chunks = total_result.count if total_result.count is not None else 0

        # Get unique sources
        try:
            sources_result = db.rpc("get_unique_sources_count").execute()
            if isinstance(sources_result.data, (int, float)):
                unique_sources = int(sources_result.data)
            elif isinstance(sources_result.data, list) and len(sources_result.data) > 0:
                unique_sources = int(sources_result.data[0])
            else:
                unique_sources = 0
        except Exception:
            sources_count = (
                db.table("sources")
                .select(
                    "id",
                    count=cast(Any, "exact"),
                )
                .limit(1)
                .execute()
            )
            unique_sources = sources_count.count if sources_count.count is not None else 0

        # Get chunks with embeddings (non-null embedding column)
        # Note: If is_processed=true, assume embedding exists
        embeddings_result = (
            db.table("document_chunks")
            .select("*", count=cast(Any, "exact"))
            .eq("is_processed", True)
            .limit(1)
            .execute()
        )
        total_embeddings = embeddings_result.count if embeddings_result.count is not None else 0

        # Get average chunk size
        try:
            avg_size_result = db.rpc("get_average_chunk_size").execute()
            avg_chunk_size = float(avg_size_result.data) if avg_size_result.data else 0.0  # type: ignore[arg-type]
        except Exception:
            sample = db.table("document_chunks").select("chunk_size").limit(500).execute()
            sample_rows: list[dict[str, Any]] = sample.data or []  # type: ignore[assignment]
            sizes = [
                int(item.get("chunk_size") or 0) for item in sample_rows if item.get("chunk_size")
            ]
            avg_chunk_size = float(sum(sizes) / len(sizes)) if sizes else 0.0

        # Get database size (if RPC function exists)
        try:
            db_size_result = db.rpc("get_database_size").execute()
            db_size_bytes: int | None = int(db_size_result.data) if db_size_result.data else None  # type: ignore[arg-type]
        except Exception:
            db_size_bytes = None

        db_stats = DatabaseStats(
            total_chunks=total_chunks,
            unique_sources=unique_sources,
            total_embeddings=total_embeddings,
            average_chunk_size=avg_chunk_size,
            db_size_bytes=db_size_bytes,
            last_updated=datetime.now(timezone.utc),
        )

        # Service metrics (basic, can be enhanced)
        services = {
            "agent_service": {"url": AGENT_SERVICE_URL, "status": "configured"},
            "embedding_service": {"url": EMBEDDING_SERVICE_URL, "status": "configured"},
        }

        return AdminStatsResponse(database=db_stats, services=services)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")


@router.get("/documents")
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source_filter: str | None = Query(None, description="Filter by source URL"),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
) -> DocumentsListResponse:
    """
    List indexed document chunks.

    Paginated, sortable by creation date or source.

    Args:
        limit: Results per page
        offset: Results to skip
        source_filter: Optional source URL filter

    Returns:
        Paginated list of document chunks
    """
    try:
        store = get_chroma_store()
        rows: list[dict[str, Any]] = []
        for row in store.iter_all_chunks(batch_size=500):
            metadata = _safe_metadata_dict(row.get("metadata"))
            source_url = str(metadata.get("source_url") or "")
            if source_filter and source_filter.lower() not in source_url.lower():
                continue
            rows.append(
                {
                    "id": row.get("id"),
                    "source_url": source_url,
                    "content": str(row.get("content") or ""),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                }
            )

        rows.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        total = len(rows)
        paged = rows[offset : offset + limit]

        documents = []
        for row in paged:
            created_at_raw = row.get("created_at")
            updated_at_raw = row.get("updated_at")
            created_at = (
                datetime.fromisoformat(str(created_at_raw).replace("Z", "+00:00"))
                if created_at_raw
                else datetime.now(timezone.utc)
            )
            updated_at = (
                datetime.fromisoformat(str(updated_at_raw).replace("Z", "+00:00"))
                if updated_at_raw
                else None
            )
            documents.append(
                DocumentChunk(
                    chunk_id=str(row.get("id")),
                    source_url=row.get("source_url", ""),
                    content_preview=(row.get("content") or "")[:200],
                    embedding_dimension=384,
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )

        page = (offset // limit) + 1

        return DocumentsListResponse(documents=documents, total=total, page=page, limit=limit)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/documents/{chunk_id}")
async def delete_document(
    chunk_id: str,
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
) -> DeleteChunkResponse:
    """
    Delete a specific document chunk.

    Removes from database and vector store.

    Args:
        chunk_id: Chunk identifier to delete

    Returns:
        Deletion confirmation
    """
    try:
        store = get_chroma_store()
        existing = store.chunks().get(ids=[chunk_id])
        if not (existing.get("ids") or []):
            raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found")

        store.delete_chunks(ids=[chunk_id])

        return DeleteChunkResponse(
            success=True,
            deleted_chunk_id=chunk_id,
            message=f"Successfully deleted chunk {chunk_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chunk: {str(e)}")


@router.post("/database/clean")
async def clean_database(
    request: CleanDatabaseRequest,
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
) -> CleanDatabaseResponse:
    """
    Truncate all document chunks and embeddings.

    DESTRUCTIVE OPERATION. Requires confirmation token to prevent accidents.

    Args:
        request: CleanDatabaseRequest with confirmation token

    Returns:
        Confirmation of deletion with count

    Raises:
        HTTPException: If confirmation token is invalid
    """
    # Validate token
    token = request.confirmation_token

    if token not in _cleanup_tokens:
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired confirmation token. Request a new token from GET /api/admin/database/clean-request",
        )

    # Check token expiry
    expires_at = _cleanup_tokens[token]
    if datetime.now(timezone.utc) > expires_at:
        del _cleanup_tokens[token]
        raise HTTPException(
            status_code=403, detail="Confirmation token has expired. Request a new token."
        )

    # Consume token (one-time use)
    del _cleanup_tokens[token]

    try:
        # Check if require_confirmation is enabled
        if ADMIN_CONFIG.get("require_confirmation", True):
            # Already validated token above
            pass

        # Get count before deletion
        count_result = (
            db.table("document_chunks")
            .select(
                "*",
                count="exact",  # type: ignore[arg-type]
            )
            .limit(1)
            .execute()
        )
        _deleted_count = count_result.count if count_result.count is not None else 0

        # Delete all chunks (in batches to avoid timeout)
        batch_size = ADMIN_CONFIG.get("delete_chunk_batch_size", 1000)
        deleted_total = 0

        while True:
            result = db.table("document_chunks").delete().limit(batch_size).execute()  # type: ignore[attr-defined]
            if not result.data:
                break
            deleted_total += len(result.data)
            if len(result.data) < batch_size:
                break

        # Also delete orphaned sources if they exist in a separate table
        # (Optional, depends on schema)
        try:
            db.table("search_queries").delete().execute()
        except Exception:
            pass  # Table might not exist or be empty

        return CleanDatabaseResponse(
            success=True,
            deleted_chunks=deleted_total,
            message=f"Database cleaned: {deleted_total} chunks deleted",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clean database: {str(e)}")


@router.get("/database/clean-request")
async def request_database_clean(_admin=Depends(_verify_admin)) -> CleanRequestTokenResponse:
    """
    Request confirmation token for database cleanup.

    Returns token that must be used in /database/clean POST.
    This is the first step of the cleanup process.

    Returns:
        Confirmation token (valid for 5 minutes)
    """
    # Generate secure token
    token = secrets.token_urlsafe(32)

    # Store with 5-minute expiry
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    _cleanup_tokens[token] = expires_at

    # Clean expired tokens
    now = datetime.now(timezone.utc)
    expired = [t for t, exp in _cleanup_tokens.items() if exp < now]
    for t in expired:
        del _cleanup_tokens[t]

    return CleanRequestTokenResponse(
        token=token, expires_at=expires_at, endpoint="POST /api/admin/database/clean"
    )


@router.get("/sources")
async def list_all_sources(
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
) -> SourcesListResponse:
    """
    List all unique source URLs in the database.

    Returns:
        List of sources with chunk counts
    """
    try:
        store = get_chroma_store()
        source_map: dict[str, dict[str, Any]] = {}

        for source in store.list_sources(limit=1000, offset=0):
            url = str(source.get("url") or "")
            if not url:
                continue
            metadata = _safe_metadata_dict(source.get("metadata"))
            source_map[url] = {
                "url": url,
                "title": source.get("title") or metadata.get("title"),
                "description": metadata.get("description"),
                "author": metadata.get("author"),
                "published_date": metadata.get("published_date"),
                "domain": metadata.get("domain") or _domain_from_url(url),
                "source_domain": metadata.get("source_domain") or _domain_from_url(url),
                "metadata": metadata,
                "tags": source.get("tags") or _extract_tags(metadata),
                "is_active": bool(source.get("is_active", True)),
                "scrape_count": _to_int(metadata.get("scrape_count"), 0),
                "reliability_score": metadata.get("reliability_score"),
                "chunk_count": 0,
                "total_chunks": 0,
                "total_characters": _to_int(metadata.get("total_characters"), 0),
                "created_at": source.get("created_at") or metadata.get("created_at"),
                "updated_at": source.get("updated_at") or metadata.get("updated_at"),
            }

        for row in store.iter_all_chunks(batch_size=500):
            metadata = _safe_metadata_dict(row.get("metadata"))
            source_url = str(metadata.get("source_url") or "")
            if not source_url:
                continue
            current = source_map.get(source_url)
            if current is None:
                current = {
                    "url": source_url,
                    "title": metadata.get("document_title"),
                    "description": metadata.get("description"),
                    "author": metadata.get("author"),
                    "published_date": metadata.get("published_date"),
                    "domain": metadata.get("source_domain") or _domain_from_url(source_url),
                    "source_domain": metadata.get("source_domain") or _domain_from_url(source_url),
                    "metadata": metadata,
                    "tags": _extract_tags(metadata),
                    "is_active": True,
                    "scrape_count": _to_int(metadata.get("scrape_count"), 0),
                    "reliability_score": metadata.get("reliability_score"),
                    "chunk_count": 0,
                    "total_chunks": 0,
                    "total_characters": _to_int(metadata.get("total_characters"), 0),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                }
                source_map[source_url] = current
            current["chunk_count"] += 1
            current["total_chunks"] = current["chunk_count"]
            if _to_int(current.get("total_characters"), 0) == 0:
                current["total_characters"] = _to_int(current.get("total_characters"), 0) + _to_int(
                    metadata.get("chunk_size"), len(str(row.get("content") or ""))
                )

        sources = [_normalize_source_row(source or {}) for source in source_map.values()]
        sources.sort(key=lambda x: x.get("chunk_count", 0), reverse=True)

        return SourcesListResponse(sources=sources, total=len(sources))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")


@router.post("/sources/validate")
async def validate_sources(
    request: ValidateSourceRequest,
    _admin=Depends(_verify_admin),
) -> ValidateSourceResponse:
    """
    Validate a source URL.

    Tests HTTP connectivity for the source.
    Admin endpoint for debugging scraping issues.

    Returns:
        Validation results
    """
    url = request.url

    try:
        # Test HTTP HEAD request first (lightweight)
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                response = await client.head(url)
                http_status = response.status_code

                # If HEAD not allowed, try GET
                if http_status == 405:
                    response = await client.get(url, timeout=10.0)
                    http_status = response.status_code

                is_accessible = 200 <= http_status < 400

                # Basic scrapability check
                is_scrapeable = is_accessible
                if is_accessible:
                    # Check content type if available
                    content_type = response.headers.get("content-type", "")
                    # Scrapeable if HTML, XML, or plain text
                    is_scrapeable = any(
                        ct in content_type.lower()
                        for ct in ["html", "xml", "text/plain", "application/pdf"]
                    )

                message = "URL is accessible"
                if is_accessible and is_scrapeable:
                    message = "URL is accessible and scrapeable"
                elif is_accessible and not is_scrapeable:
                    message = (
                        f"URL is accessible but content type ({content_type}) may not be scrapeable"
                    )
                elif not is_accessible:
                    message = f"URL returned HTTP {http_status}"

                return ValidateSourceResponse(
                    url=url,
                    is_accessible=is_accessible,
                    is_scrapeable=is_scrapeable,
                    http_status=http_status,
                    message=message,
                )

            except httpx.TimeoutException:
                return ValidateSourceResponse(
                    url=url,
                    is_accessible=False,
                    is_scrapeable=False,
                    http_status=None,
                    message="Request timed out after 10 seconds",
                )
            except httpx.HTTPError as e:
                return ValidateSourceResponse(
                    url=url,
                    is_accessible=False,
                    is_scrapeable=False,
                    http_status=None,
                    message=f"HTTP error: {str(e)}",
                )

    except Exception as e:
        return ValidateSourceResponse(
            url=url,
            is_accessible=False,
            is_scrapeable=False,
            http_status=None,
            message=f"Validation failed: {str(e)}",
        )


@router.get("/config")
async def get_admin_config():
    """
    Get gateway admin configuration.

    Returns:
        Current admin settings
    """
    return {"config": ADMIN_CONFIG}


@router.post("/config")
async def update_admin_config(require_confirmation: bool | None = None):
    """
    Update gateway admin configuration.

    Args:
        require_confirmation: Whether to require confirmation tokens for destructive ops

    Returns:
        Updated configuration
    """
    if require_confirmation is not None:
        ADMIN_CONFIG["require_confirmation"] = require_confirmation

    return {"config": ADMIN_CONFIG}


@router.get("/diagnostics/schema")
async def schema_diagnostics(db: Client = Depends(get_database_client)) -> dict[str, Any]:
    """
    Diagnose database schema prerequisites for Vecinita.

    Validates:
    - RPC function: search_similar_documents exists
    - Table: document_chunks exists
    - Column: embedding column exists with pgvector(384) type
    - Indexes: Required indexes exist on document_chunks
    - Supporting tables: conversations, documents exist

    Returns:
        {
            'status': 'ok' | 'warning' | 'error',
            'summary': String summary of issues,
            'errors': List of blocking errors,
            'warnings': List of non-blocking warnings,
            'checks': Detailed results for each check
        }

    Use this endpoint to verify your Supabase schema is correctly configured
    before deploying Vecinita to production.
    """
    try:
        result = await validate_schema(db)
        result["summary"] = get_validation_summary(result)
        return result
    except Exception as e:
        logger.error(f"Schema diagnostics error: {e}")
        return {
            "status": "error",
            "summary": f"Schema diagnostics failed: {str(e)}",
            "errors": [str(e)],
            "warnings": [],
            "checks": {},
        }


# ============================================================================
# Model configuration (LLM + Embeddings)
# ============================================================================


class AgentModelSelectionRequest(BaseModel):
    provider: str
    model: str | None = None
    lock: bool | None = None


class EmbeddingSelectionRequest(BaseModel):
    provider: str
    model: str
    lock: bool | None = None


class AdminModelConfigUpdateRequest(BaseModel):
    generation: AgentModelSelectionRequest | None = None
    embeddings: EmbeddingSelectionRequest | None = None


@router.get("/models/config")
async def get_models_config(_admin=Depends(_verify_admin)):
    """Get current generation and embedding model selections."""
    payload: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            agent_resp = await client.get(f"{AGENT_SERVICE_URL}/model-selection")
            agent_resp.raise_for_status()
            payload["generation"] = agent_resp.json()

            embed_resp = await client.get(
                f"{EMBEDDING_SERVICE_URL}/config",
                headers=_embedding_service_headers(),
            )
            embed_resp.raise_for_status()
            payload["embeddings"] = embed_resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch model config: {exc}")

    return payload


@router.post("/models/config")
async def update_models_config(
    request: AdminModelConfigUpdateRequest,
    _admin=Depends(_verify_admin),
):
    """Update generation and/or embedding model selection."""
    if request.generation is None and request.embeddings is None:
        raise HTTPException(
            status_code=400, detail="Provide at least one of generation or embeddings"
        )

    result: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if request.generation is not None:
                generation_payload = request.generation.model_dump(exclude_none=True)
                generation_resp = await client.post(
                    f"{AGENT_SERVICE_URL}/model-selection",
                    json=generation_payload,
                )
                generation_resp.raise_for_status()
                result["generation"] = generation_resp.json()

            if request.embeddings is not None:
                embedding_payload = request.embeddings.model_dump(exclude_none=True)
                embedding_resp = await client.post(
                    f"{EMBEDDING_SERVICE_URL}/config",
                    json=embedding_payload,
                    headers=_embedding_service_headers(),
                )
                embedding_resp.raise_for_status()
                result["embeddings"] = embedding_resp.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(
            status_code=exc.response.status_code if exc.response else 502, detail=detail
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to update model config: {exc}")

    return {"status": "ok", **result}


# ============================================================================
# Source management — add URL to corpus, delete, list queue
# ============================================================================


def _source_job_file_path(url: str, depth: int) -> str:
    return f"url::{depth}::{url}"


async def _extract_text_from_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {exc}")

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Source returned HTTP {response.status_code}")

    content_type = (response.headers.get("content-type") or "").lower()
    if "html" in content_type or "xml" in content_type:
        from bs4 import BeautifulSoup

        return BeautifulSoup(response.text, "html.parser").get_text(separator="\n")

    return response.text


def _chunk_text_content(text: str) -> list[str]:
    from langchain_text_splitters import (  # type: ignore[import-not-found]
        RecursiveCharacterTextSplitter,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)  # type: ignore[no-any-return]


async def _embed_text_chunks(chunks: list[str]) -> list[list[float]]:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            embed_resp = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed-batch",
                json={"texts": chunks},
                headers=_embedding_service_headers(),
            )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding service error: {exc}")

    if embed_resp.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"Embedding service returned {embed_resp.status_code}"
        )

    embeddings: list[list[float]] = embed_resp.json().get("embeddings", [])
    if len(embeddings) != len(chunks):
        raise HTTPException(status_code=502, detail="Embedding count mismatch.")

    return embeddings


def _validate_source_url(url: str) -> str:
    import re as _re

    normalized = (url or "").strip()
    if not _re.match(r"^https?://", normalized):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    return normalized


def _should_retry_with_scraper_loader(exc: HTTPException) -> bool:
    detail = str(exc.detail or "").lower()
    anti_bot_markers = [
        "http 403",
        "forbidden",
        "access denied",
        "cloudflare",
        "captcha",
        "bot",
    ]
    return any(marker in detail for marker in anti_bot_markers)


async def _ingest_source_via_scraper_loader(url: str, depth: int) -> dict[str, Any]:
    temp_dir = os.path.join(tempfile.gettempdir(), "vecinita_admin_ingest_fallback")
    os.makedirs(temp_dir, exist_ok=True)

    file_suffix = hashlib.sha256(f"{url}:{time.time()}".encode()).hexdigest()[:12]
    output_file = os.path.join(temp_dir, f"source_{file_suffix}_chunks.jsonl")
    failed_log = os.path.join(temp_dir, f"source_{file_suffix}_failed.log")

    scraper = VecinaScraper(
        output_file=output_file,
        failed_log=failed_log,
        links_file=None,
        stream_mode=True,
    )

    await asyncio.to_thread(scraper.scrape_urls, [url], "playwright")
    await asyncio.to_thread(scraper.finalize)

    if url not in scraper.successful_sources:
        failure_reason = scraper.failed_sources.get(url) or "Scraper loader fallback failed"
        raise HTTPException(status_code=502, detail=f"Scraper fallback failed: {failure_reason}")

    total_chunks = int(scraper.stats.get("total_chunks", 0))
    total_uploads = int(scraper.stats.get("total_uploads", 0))

    return {
        "chunks_total": total_chunks,
        "chunks_inserted": total_uploads if total_uploads > 0 else total_chunks,
        "ingestion_path": "scraper_loader_fallback",
        "depth": depth,
    }


async def _ingest_source_url(url: str, depth: int, normalized_tags: list[str]) -> dict[str, Any]:
    source_domain = _domain_from_url(url)
    source_title = source_domain or url
    job_id = hashlib.sha256(f"{url}:{depth}:{time.time()}".encode()).hexdigest()
    created_at = datetime.now(timezone.utc).isoformat()
    started_at = datetime.now(timezone.utc).isoformat()

    try:
        store = get_chroma_store()
        store.upsert_source(
            url=url,
            metadata={
                "tags": normalized_tags,
                "source_type": "web",
                "depth": depth,
                "source_domain": source_domain,
                "created_at": created_at,
                "updated_at": created_at,
            },
            title=source_title,
            is_active=True,
        )
        store.add_queue_job(
            job_id=job_id,
            payload={
                "url": url,
                "depth": depth,
                "status": "pending",
                "created_at": created_at,
                "file_path": _source_job_file_path(url, depth),
            },
        )

        store.add_queue_job(
            job_id=job_id,
            payload={
                "url": url,
                "depth": depth,
                "status": "processing",
                "created_at": created_at,
                "started_at": started_at,
                "chunks_processed": 0,
                "total_chunks": 0,
                "file_path": _source_job_file_path(url, depth),
            },
        )

        total_chunks = 0
        inserted = 0
        total_characters = 0
        ingestion_path = "direct_fetch"

        try:
            text = (await _extract_text_from_url(url)).strip()
            if not text:
                raise HTTPException(
                    status_code=422, detail="No text could be extracted from the URL."
                )

            chunks = _chunk_text_content(text)
            if not chunks:
                raise HTTPException(
                    status_code=422, detail="URL content produced no chunks after splitting."
                )

            embeddings = await _embed_text_chunks(chunks)

            total_chunks = len(chunks)
            total_characters = len(text)
            rows: list[dict[str, Any]] = []
            for index, chunk_text in enumerate(chunks):
                chunk_id = hashlib.sha256(f"{url}:{index}:{chunk_text}".encode()).hexdigest()
                rows.append(
                    {
                        "id": chunk_id,
                        "content": chunk_text,
                        "embedding": embeddings[index],
                        "metadata": {
                            "source_url": url,
                            "source_domain": source_domain,
                            "document_title": source_title,
                            "chunk_index": index,
                            "total_chunks": total_chunks,
                            "chunk_size": len(chunk_text),
                            "tags": normalized_tags,
                            "source_type": "web",
                            "depth": depth,
                            "created_at": created_at,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        },
                        "source_url": url,
                        "source_domain": source_domain,
                        "chunk_index": index,
                        "total_chunks": total_chunks,
                        "chunk_size": len(chunk_text),
                        "document_title": source_title,
                        "created_at": created_at,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "is_processed": True,
                        "processing_status": "completed",
                    }
                )

            inserted = store.upsert_chunks(rows)
        except HTTPException as direct_exc:
            if not _should_retry_with_scraper_loader(direct_exc):
                raise

            logger.info(
                "Direct source fetch blocked for %s (%s). Retrying via scraper loader fallback.",
                url,
                direct_exc.detail,
            )
            fallback_result = await _ingest_source_via_scraper_loader(url, depth)
            total_chunks = int(fallback_result.get("chunks_total", 0))
            inserted = int(fallback_result.get("chunks_inserted", total_chunks))
            ingestion_path = str(fallback_result.get("ingestion_path") or "scraper_loader_fallback")

        completed_at = datetime.now(timezone.utc).isoformat()

        store.upsert_source(
            url=url,
            metadata={
                "tags": normalized_tags,
                "source_type": "web",
                "depth": depth,
                "source_domain": source_domain,
                "scrape_count": 1,
                "total_characters": total_characters,
                "last_scraped_at": completed_at,
                "ingestion_path": ingestion_path,
                "updated_at": completed_at,
            },
            title=source_title,
            is_active=True,
        )

        store.add_queue_job(
            job_id=job_id,
            payload={
                "url": url,
                "depth": depth,
                "status": "completed",
                "created_at": created_at,
                "started_at": started_at,
                "completed_at": completed_at,
                "chunks_processed": inserted,
                "total_chunks": total_chunks,
                "file_path": _source_job_file_path(url, depth),
            },
        )

        return {
            "status": "completed",
            "url": url,
            "depth": depth,
            "tags": normalized_tags,
            "chunks_total": total_chunks,
            "chunks_inserted": inserted,
            "job_id": job_id,
        }
    except HTTPException as http_exc:
        try:
            store = get_chroma_store()
            store.add_queue_job(
                job_id=job_id,
                payload={
                    "url": url,
                    "depth": depth,
                    "status": "failed",
                    "created_at": created_at,
                    "started_at": started_at,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "chunks_processed": 0,
                    "total_chunks": 0,
                    "error_message": str(http_exc.detail),
                    "file_path": _source_job_file_path(url, depth),
                },
            )
        except Exception:
            logger.exception("Failed to update queue state after source ingestion HTTPException")
        raise
    except Exception as exc:
        try:
            store = get_chroma_store()
            store.add_queue_job(
                job_id=job_id,
                payload={
                    "url": url,
                    "depth": depth,
                    "status": "failed",
                    "created_at": created_at,
                    "started_at": started_at,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "chunks_processed": 0,
                    "total_chunks": 0,
                    "error_message": str(exc),
                    "file_path": _source_job_file_path(url, depth),
                },
            )
        except Exception:
            logger.exception("Failed to update queue state after source ingestion exception")
        raise HTTPException(status_code=500, detail=f"Failed to process URL source: {exc}")


@router.post("/sources")
async def add_source(
    url: str = Form(..., description="URL to scrape and embed"),
    depth: int = Form(1, ge=1, le=5, description="Crawl depth"),
    tags: str | None = Form(None, description="Comma-separated metadata tags"),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """Add a URL source and run ingestion (fetch, chunk, embed, upsert). Requires admin auth."""
    validated_url = _validate_source_url(url)
    normalized_tags = parse_tags_input(tags)
    return await _ingest_source_url(validated_url, depth, normalized_tags)


@router.post("/sources/batch")
async def add_sources_batch(
    request: BatchSourceIngestRequest,
    _admin=Depends(_verify_admin),
):
    """Bulk ingest URL sources from pasted urls.txt content and/or explicit URL list."""
    if request.depth < 1 or request.depth > 5:
        raise HTTPException(status_code=400, detail="Depth must be between 1 and 5")

    parsed_urls = _parse_urls_text(request.urls_text, request.urls)
    if not parsed_urls:
        raise HTTPException(status_code=400, detail="Provide at least one URL in urls_text or urls")

    baseline_tags = normalize_tags(request.tags)
    tag_mode = request.tag_mode or "auto_infer"

    results: list[dict[str, Any]] = []
    for raw_url in parsed_urls:
        validated_url = _validate_source_url(raw_url)
        tags_for_url = baseline_tags if tag_mode in ["baseline_only", "auto_infer"] else []
        try:
            result = await _ingest_source_url(validated_url, request.depth, tags_for_url)
            results.append({"url": validated_url, "status": "completed", "result": result})
        except HTTPException as exc:
            results.append(
                {
                    "url": validated_url,
                    "status": "failed",
                    "error": str(exc.detail),
                }
            )

    completed = len([item for item in results if item["status"] == "completed"])
    failed = len(results) - completed

    return {
        "status": "completed" if failed == 0 else "partial",
        "submitted": len(parsed_urls),
        "completed": completed,
        "failed": failed,
        "depth": request.depth,
        "tag_mode": tag_mode,
        "baseline_tags": baseline_tags,
        "results": results,
    }


@router.patch("/sources/tags")
async def update_source_tags(
    request: SourceTagsUpdateRequest,
    lang: str | None = Query(None, description="Response language (en/es)"),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """Update source-level metadata tags and propagate to existing chunks."""
    normalized_tags = normalize_tags(request.tags)

    try:
        store = get_chroma_store()
        existing = store.get_source(request.url)
        source_metadata = _safe_metadata_dict(existing.get("metadata") if existing else {})
        source_metadata["tags"] = normalized_tags
        store.upsert_source(
            url=request.url,
            metadata=source_metadata,
            title=(existing or {}).get("title") if isinstance(existing, dict) else request.url,
            is_active=True,
        )

        chunk_result = store.get_chunks(where={"source_url": request.url}, limit=5000, offset=0)
        ids = chunk_result.get("ids") or []
        docs = chunk_result.get("documents") or []
        metas = chunk_result.get("metadatas") or []

        rows: list[dict[str, Any]] = []
        for idx, chunk_id in enumerate(ids):
            metadata = _safe_metadata_dict(metas[idx] if idx < len(metas) else {})
            metadata["tags"] = normalized_tags
            rows.append(
                {
                    "id": chunk_id,
                    "content": docs[idx] if idx < len(docs) and docs[idx] is not None else "",
                    "embedding": [0.0],
                    "metadata": metadata,
                    "source_url": metadata.get("source_url", request.url),
                    "source_domain": metadata.get("source_domain", ""),
                    "chunk_index": metadata.get("chunk_index", idx),
                    "total_chunks": metadata.get("total_chunks", len(ids)),
                    "chunk_size": metadata.get("chunk_size", 0),
                    "document_title": metadata.get("document_title", ""),
                    "created_at": metadata.get("created_at"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "is_processed": metadata.get("is_processed", True),
                    "processing_status": metadata.get("processing_status", "completed"),
                }
            )

        updated = len(rows)
        if rows:
            # Preserve existing vectors by fetching them directly from collection.
            existing_vectors_payload = (
                store.chunks().get(ids=ids, include=["embeddings"]).get("embeddings")
            )
            if existing_vectors_payload is None:
                existing_vectors: list[Any] = []
            else:
                existing_vectors = list(existing_vectors_payload)
            for idx, row in enumerate(rows):
                vector: Any = existing_vectors[idx] if idx < len(existing_vectors) else None
                if hasattr(vector, "tolist"):
                    vector = vector.tolist()
                if vector is None:
                    row["embedding"] = [0.0]
                elif isinstance(vector, list) and len(vector) == 0:
                    row["embedding"] = [0.0]
                else:
                    row["embedding"] = vector
            store.upsert_chunks(rows)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{_tagging_message('tags_update_failed', _normalize_lang(lang))}: {exc}",
        )

    return {
        "status": "updated",
        "message": _tagging_message("tags_updated", _normalize_lang(lang)),
        "url": request.url,
        "tags": normalized_tags,
        "chunks_updated": updated,
    }


@router.get("/tags")
async def get_metadata_tags(
    query: str | None = Query(None, description="Optional tag prefix filter"),
    limit: int = Query(100, ge=1, le=500),
    lang: str | None = Query(None, description="Response language (en/es)"),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """Return distinct metadata tags for autocomplete in admin UI."""
    try:
        store = get_chroma_store()
        seen: set[str] = set()
        query_norm = (query or "").strip().lower()
        for row in store.iter_all_chunks(batch_size=500):
            metadata = _safe_metadata_dict(row.get("metadata"))
            for tag in _extract_tags(metadata):
                if query_norm and not tag.startswith(query_norm):
                    continue
                seen.add(tag)
        tags = sorted(seen)[:limit]
        return {"tags": tags, "total": len(tags)}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{_tagging_message('tags_fetch_failed', _normalize_lang(lang))}: {exc}",
        )


@router.delete("/sources")
async def delete_source(
    url: str = Query(..., description="Source URL to remove"),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """Delete all chunks and source record for a URL. Requires admin auth."""
    deleted_chunks = 0
    try:
        store = get_chroma_store()
        chunk_result = store.get_chunks(where={"source_url": url}, limit=5000, offset=0)
        ids = chunk_result.get("ids") or []
        if ids:
            store.delete_chunks(ids=ids)
            deleted_chunks = len(ids)
        store.delete_source(url)
    except Exception as exc:
        logger.warning(f"Source delete failed for {url}: {exc}")

    return {"status": "deleted", "url": url, "chunks_deleted": deleted_chunks}


@router.get("/queue")
async def get_queue(
    status: str | None = Query(
        None, description="Filter by status: pending|processing|completed|failed"
    ),
    limit: int = Query(50, ge=1, le=200),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """Return scraper job queue. Requires admin auth."""
    try:
        store = get_chroma_store()
        normalized_status = "completed" if status == "done" else status
        rows = store.list_queue_jobs(status=normalized_status, limit=limit)
        jobs: list[dict[str, Any]] = []
        for row in rows:
            parsed = _parse_queue_file_path(str(row.get("file_path") or ""))
            jobs.append(
                {
                    "id": row.get("id"),
                    "status": row.get("status"),
                    "created_at": row.get("created_at"),
                    "started_at": row.get("started_at"),
                    "completed_at": row.get("completed_at"),
                    "chunks_processed": row.get("chunks_processed") or 0,
                    "total_chunks": row.get("total_chunks") or 0,
                    "error": row.get("error_message"),
                    "file_path": parsed.get("file_path"),
                    "url": row.get("url") or parsed.get("url"),
                    "depth": row.get("depth") or parsed.get("depth"),
                    "job_type": parsed.get("type"),
                }
            )
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/queue/status-summary")
async def get_queue_status_summary(
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """Return aggregated processing queue status summary from v_processing_status view."""
    try:
        result = (
            db.table("v_processing_status")
            .select("status,job_count,total_chunks_processed,avg_processing_time_seconds")
            .order("status")
            .execute()
        )
        rows: list[dict[str, Any]] = result.data or []  # type: ignore[assignment]
        total_jobs = sum(int(item.get("job_count") or 0) for item in rows)
        return {
            "statuses": rows,
            "total_jobs": total_jobs,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch queue status summary: {exc}")


@router.get("/stats/chunk-domains")
async def get_chunk_domain_stats(
    limit: int = Query(50, ge=1, le=500),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """Return per-domain chunk statistics from v_chunk_statistics view."""
    try:
        store = get_chroma_store()
        buckets: dict[str, dict[str, Any]] = {}
        for row in store.iter_all_chunks(batch_size=500):
            metadata = _safe_metadata_dict(row.get("metadata"))
            source_domain = str(metadata.get("source_domain") or "unknown")
            source_url = str(metadata.get("source_url") or "")
            content = str(row.get("content") or "")
            chunk_size = int(metadata.get("chunk_size") or len(content))

            current = buckets.get(source_domain)
            if current is None:
                current = {
                    "source_domain": source_domain,
                    "chunk_count": 0,
                    "total_size": 0,
                    "latest_chunk": metadata.get("updated_at") or metadata.get("created_at"),
                    "_sources": set(),
                }
                buckets[source_domain] = current
            current["chunk_count"] += 1
            current["total_size"] += chunk_size
            if source_url:
                current["_sources"].add(source_url)

        rows: list[dict[str, Any]] = []
        for item in buckets.values():
            chunk_count = int(item.get("chunk_count") or 0)
            rows.append(
                {
                    "source_domain": item.get("source_domain"),
                    "chunk_count": chunk_count,
                    "avg_chunk_size": (
                        int(item.get("total_size", 0) / chunk_count) if chunk_count else 0
                    ),
                    "total_size": item.get("total_size", 0),
                    "document_count": len(item.get("_sources", set())),
                    "latest_chunk": item.get("latest_chunk"),
                }
            )
        rows.sort(key=lambda item: int(item.get("chunk_count") or 0), reverse=True)
        rows = rows[:limit]
        return {"rows": rows, "total": len(rows)}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch chunk domain statistics: {exc}"
        )


# ============================================================================
# Document upload — PDF / TXT / HTML → chunk → embed → insert
# ============================================================================

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
ALLOWED_TYPES = {"application/pdf", "text/plain", "text/html", "text/markdown"}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".html", ".htm", ".md"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    tags: str | None = Form(None, description="Comma-separated metadata tags"),
    db: Client = Depends(get_database_client),
    _admin=Depends(_verify_admin),
):
    """
    Upload a document (PDF, TXT, HTML, MD) to be chunked, embedded, and stored.
    FAQs can be uploaded as a plain .txt file.
    Requires admin auth.
    """
    import pathlib

    # ── Validate ─────────────────────────────────────────────────────────
    ext = pathlib.Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    raw = await file.read()
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max: {MAX_UPLOAD_MB} MB",
        )

    # ── Extract text ──────────────────────────────────────────────────────
    text = ""
    try:
        if ext == ".pdf":
            import pypdf  # type: ignore[import-not-found]

            reader = pypdf.PdfReader(io.BytesIO(raw))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext in (".html", ".htm"):
            from bs4 import BeautifulSoup

            text = BeautifulSoup(raw, "html.parser").get_text(separator="\n")
        else:
            text = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Text extraction failed: {exc}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the file.")

    # ── Chunk ─────────────────────────────────────────────────────────────
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks: list[str] = splitter.split_text(text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chunking failed: {exc}")

    if not chunks:
        raise HTTPException(status_code=422, detail="Document produced no chunks after splitting.")

    # ── Embed via embedding service ───────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            embed_resp = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed-batch",
                json={"texts": chunks},
                headers=_embedding_service_headers(),
            )
        if embed_resp.status_code != 200:
            raise RuntimeError(f"Embedding service returned {embed_resp.status_code}")
        embeddings: list[list[float]] = embed_resp.json().get("embeddings", [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Embedding service error: {exc}")

    if len(embeddings) != len(chunks):
        raise HTTPException(status_code=502, detail="Embedding count mismatch.")

    # ── Persist chunks and source metadata into Chroma ─────────────────────
    safe_name = (file.filename or "upload.bin").replace("/", "_")
    storage_path = (
        f"uploads/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{int(time.time())}_{safe_name}"
    )
    source_url = f"upload://{storage_path}"
    normalized_tags = parse_tags_input(tags)
    public_download_url: str | None = None
    storage_bucket = UPLOAD_STORAGE_BUCKET
    storage_uploaded = False

    try:
        content_type = file.content_type or "application/octet-stream"
        db.storage.from_(storage_bucket).upload(
            storage_path,
            raw,
            {"content-type": content_type, "upsert": "true"},
        )
        public_url_payload = db.storage.from_(storage_bucket).get_public_url(storage_path)
        if isinstance(public_url_payload, str):
            public_download_url = public_url_payload
        elif isinstance(public_url_payload, dict):
            public_download_url = (
                public_url_payload.get("publicUrl")
                or public_url_payload.get("publicURL")
                or public_url_payload.get("public_url")
            )
        storage_uploaded = bool(public_download_url)
    except Exception as exc:
        logger.warning(
            "Failed to upload %s to storage bucket '%s': %s",
            file.filename,
            storage_bucket,
            exc,
        )

    store = get_chroma_store()
    try:
        store.upsert_source(
            url=source_url,
            title=file.filename,
            metadata={
                "tags": normalized_tags,
                "source_type": "upload",
                "storage_uploaded": storage_uploaded,
                "storage_bucket": storage_bucket if storage_uploaded else None,
                "storage_path": storage_path if storage_uploaded else None,
                "download_url": public_download_url,
                "mime_type": file.content_type,
            },
            is_active=True,
        )
    except Exception as exc:
        logger.warning("Failed to upsert upload source metadata for %s: %s", source_url, exc)

    total_chunks = len(chunks)
    inserted = 0
    errors: list[str] = []

    rows: list[dict[str, Any]] = []
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
        rows.append(
            {
                "id": hashlib.sha256(f"{source_url}:{i}:{chunk_text}".encode()).hexdigest(),
                "content": chunk_text,
                "embedding": embedding,
                "source_url": source_url,
                "source_domain": "upload",
                "chunk_index": i,
                "total_chunks": total_chunks,
                "chunk_size": len(chunk_text),
                "document_title": file.filename,
                "is_processed": True,
                "processing_status": "done",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "tags": normalized_tags,
                    "source_type": "upload",
                    "storage_uploaded": storage_uploaded,
                    "storage_bucket": storage_bucket if storage_uploaded else None,
                    "storage_path": storage_path if storage_uploaded else None,
                    "download_url": public_download_url,
                    "mime_type": file.content_type,
                    "document_title": file.filename,
                },
            }
        )

    try:
        inserted = store.upsert_chunks(rows)
    except Exception as exc:
        errors.append(str(exc))

    return {
        "status": "ok" if not errors else "partial",
        "filename": file.filename,
        "chunks_total": total_chunks,
        "chunks_inserted": inserted,
        "tags": normalized_tags,
        "storage_bucket": storage_bucket if storage_uploaded else None,
        "download_url": public_download_url,
        "storage_path": storage_path if storage_uploaded else None,
        "errors": errors[:10],  # cap error list
    }
