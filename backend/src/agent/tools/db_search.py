"""Database search tool for Vecinita agent backed by Postgres/Supabase."""

import json
import logging
import os
import re
import threading
import time
from collections import OrderedDict
from contextvars import ContextVar, Token
from typing import Any

from langchain_core.tools import tool

try:
    import psycopg2
except Exception:  # pragma: no cover - optional dependency in some test/runtime profiles
    psycopg2 = None  # type: ignore[assignment]

try:
    from supabase import create_client
except Exception:  # pragma: no cover - optional dependency in some test/runtime profiles
    create_client = None  # type: ignore[assignment]

from src import config as app_config
from src.utils.tags import infer_tags_from_text, normalize_tags

logger = logging.getLogger(__name__)
_LAST_SEARCH_STATUS = "not_run"
_LAST_SEARCH_METRICS: dict[str, Any] = {}
_LAST_SEARCH_METRICS_LOCK = threading.Lock()

_SEARCH_OPTIONS: ContextVar[dict[str, Any] | None] = ContextVar(
    "db_search_options",
    default=None,
)

_SEARCH_METRICS: ContextVar[dict[str, Any] | None] = ContextVar(
    "db_search_metrics",
    default=None,
)

_SUPABASE_CLIENT = None


def _update_search_status(status: str) -> None:
    global _LAST_SEARCH_STATUS
    _LAST_SEARCH_STATUS = str(status)
    current = dict(_SEARCH_OPTIONS.get() or {})
    current["last_search_status"] = status
    _SEARCH_OPTIONS.set(current)


def get_last_search_status() -> str:
    scoped_options = _SEARCH_OPTIONS.get() or {}
    scoped = scoped_options.get("last_search_status")
    if scoped:
        return str(scoped)
    return str(_LAST_SEARCH_STATUS)


def get_last_search_metrics() -> dict[str, Any]:
    """Return metrics from the most recent db_search invocation in this process."""
    scoped = _SEARCH_METRICS.get() or {}
    if scoped:
        return dict(scoped)
    with _LAST_SEARCH_METRICS_LOCK:
        return dict(_LAST_SEARCH_METRICS)


def _update_search_metrics(metrics: dict[str, Any]) -> None:
    global _LAST_SEARCH_METRICS
    metrics_copy = dict(metrics)
    _SEARCH_METRICS.set(metrics_copy)
    with _LAST_SEARCH_METRICS_LOCK:
        _LAST_SEARCH_METRICS = metrics_copy


def set_search_options(
    *,
    tags: list[str] | None = None,
    tag_match_mode: str = "any",
    include_untagged_fallback: bool = True,
    rerank: bool = False,
    rerank_top_k: int = 10,
) -> Token:
    safe_mode = "all" if str(tag_match_mode).lower() == "all" else "any"
    safe_tags = [tag for tag in (tags or []) if isinstance(tag, str) and tag]
    return _SEARCH_OPTIONS.set(
        {
            "tags": safe_tags,
            "tag_match_mode": safe_mode,
            "include_untagged_fallback": bool(include_untagged_fallback),
            "rerank": bool(rerank),
            "rerank_top_k": max(1, min(int(rerank_top_k or 10), 50)),
            "last_search_status": "not_run",
        }
    )


def reset_search_options(token: Token) -> None:
    _SEARCH_OPTIONS.reset(token)


def _tokenize_for_rerank(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 1}


def _rerank_results(query: str, docs: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    query_terms = _tokenize_for_rerank(query)
    if not query_terms:
        return docs[:top_k]

    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in docs:
        content_terms = _tokenize_for_rerank(doc.get("content", ""))
        overlap = len(query_terms & content_terms)
        recall = overlap / max(1, len(query_terms))
        base_similarity = float(doc.get("similarity", 0.0) or 0.0)
        combined = (0.75 * base_similarity) + (0.25 * recall)
        scored.append((combined, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def _fallback_reads_enabled() -> bool:
    return os.getenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true").lower() in {"1", "true", "yes"}


def _postgres_reads_enabled() -> bool:
    return app_config.postgres_data_reads_enabled()


def _get_supabase_client():
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is not None:
        return _SUPABASE_CLIENT
    if create_client is None:
        return None

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )
    if not supabase_url or not supabase_key:
        return None

    try:
        _SUPABASE_CLIENT = create_client(supabase_url, supabase_key)
    except Exception as exc:
        logger.warning("Supabase fallback client init failed: %s", exc)
        _SUPABASE_CLIENT = None
    return _SUPABASE_CLIENT


def _normalize_supabase_document(doc: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}  # type: ignore[assignment]
    return {
        "content": doc.get("content") or "",
        "source_url": doc.get("source_url") or metadata.get("source_url") or "Unknown source",
        "source_domain": doc.get("source_domain") or metadata.get("source_domain") or "",
        "similarity": float(doc.get("similarity", 0.0) or 0.0),
        "chunk_index": (
            doc.get("chunk_index")
            if doc.get("chunk_index") is not None
            else metadata.get("chunk_index")
        ),
        "total_chunks": (
            doc.get("total_chunks")
            if doc.get("total_chunks") is not None
            else metadata.get("total_chunks")
        ),
        "chunk_size": (
            doc.get("chunk_size")
            if doc.get("chunk_size") is not None
            else metadata.get("chunk_size")
        ),
        "document_id": doc.get("id") or doc.get("document_id"),
        "document_title": doc.get("document_title") or metadata.get("document_title"),
        "created_at": doc.get("created_at") or metadata.get("created_at"),
        "updated_at": doc.get("updated_at") or metadata.get("updated_at"),
        "scraped_at": doc.get("scraped_at") or metadata.get("scraped_at"),
        "is_processed": doc.get("is_processed", metadata.get("is_processed", True)),
        "processing_status": doc.get("processing_status") or metadata.get("processing_status"),
        "error_message": doc.get("error_message"),
        "char_start": metadata.get("char_start"),
        "char_end": metadata.get("char_end"),
        "doc_index": metadata.get("doc_index"),
        "metadata": metadata,
    }


def _query_supabase_fallback(
    *,
    query_embedding: list[float],
    match_threshold: float,
    match_count: int,
    tags: list[str],
    tag_mode: str,
    include_untagged_fallback: bool,
) -> list[dict[str, Any]]:
    if not _fallback_reads_enabled():
        return []

    client = _get_supabase_client()
    if client is None:
        return []

    rpc_params: dict[str, Any] = {
        "query_embedding": query_embedding,
        "match_threshold": float(match_threshold),
        "match_count": max(int(match_count), 1),
    }
    if tags:
        rpc_params.update(
            {
                "tag_filter": tags,
                "tag_match_mode": "all" if str(tag_mode).lower() == "all" else "any",
                "include_untagged_fallback": bool(include_untagged_fallback),
            }
        )

    try:
        result = client.rpc("search_similar_documents", rpc_params).execute()
    except Exception as rpc_error:
        if "tag_filter" in rpc_params and any(
            marker in str(rpc_error).lower()
            for marker in ["does not exist", "could not find", "unexpected", "signature"]
        ):
            fallback_params = {
                "query_embedding": query_embedding,
                "match_threshold": float(match_threshold),
                "match_count": max(int(match_count), 1),
            }
            result = client.rpc("search_similar_documents", fallback_params).execute()
        else:
            raise

    rows = result.data or []
    return [_normalize_supabase_document(row) for row in rows if isinstance(row, dict)]


def _query_postgres_fallback(
    *,
    query_embedding: list[float],
    match_threshold: float,
    match_count: int,
    tags: list[str],
    tag_mode: str,
    include_untagged_fallback: bool,
) -> list[dict[str, Any]]:
    if not _postgres_reads_enabled():
        return []

    if psycopg2 is None:
        return []

    database_url = (app_config.DATABASE_URL or os.getenv("DATABASE_URL") or "").strip()
    if not database_url:
        return []

    vector_literal = "[" + ",".join(f"{float(v):.10f}" for v in query_embedding) + "]"
    params: list[Any] = [
        vector_literal,
        vector_literal,
        float(match_threshold),
    ]

    tag_condition_sql = ""
    if tags:
        if str(tag_mode).lower() == "all":
            tag_condition_sql = (
                " AND ("
                "(SELECT COUNT(DISTINCT tag) "
                " FROM unnest(%s::text[]) AS tag "
                " WHERE COALESCE(dc.metadata->'tags', '[]'::jsonb) ? tag) = cardinality(%s::text[])"
            )
            params.extend([tags, tags])
            if include_untagged_fallback:
                tag_condition_sql += (
                    " OR dc.metadata->'tags' IS NULL"
                    " OR jsonb_array_length(COALESCE(dc.metadata->'tags', '[]'::jsonb)) = 0"
                )
            tag_condition_sql += ")"
        else:
            tag_condition_sql = " AND (COALESCE(dc.metadata->'tags', '[]'::jsonb) ?| %s::text[]"
            params.append(tags)
            if include_untagged_fallback:
                tag_condition_sql += (
                    " OR dc.metadata->'tags' IS NULL"
                    " OR jsonb_array_length(COALESCE(dc.metadata->'tags', '[]'::jsonb)) = 0"
                )
            tag_condition_sql += ")"

    sql = (
        "SELECT dc.id, dc.content, dc.source_url, dc.chunk_index, dc.metadata, "
        "1 - (dc.embedding <=> %s::vector) AS similarity "
        "FROM document_chunks dc "
        "WHERE dc.embedding IS NOT NULL "
        "AND COALESCE(dc.is_processed, true) = true "
        "AND 1 - (dc.embedding <=> %s::vector) > %s"
        f"{tag_condition_sql} "
        "ORDER BY dc.embedding <=> %s::vector "
        "LIMIT %s"
    )
    params.extend([vector_literal, max(int(match_count), 1)])

    try:
        connect_timeout = max(int(os.getenv("DB_SEARCH_POSTGRES_CONNECT_TIMEOUT_SECONDS", "5")), 1)
        with psycopg2.connect(database_url, connect_timeout=connect_timeout) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description or []]
    except Exception as exc:
        logger.warning("Postgres fallback query failed: %s", exc)
        return []

    docs: list[dict[str, Any]] = []
    for row in rows:
        record = dict(zip(columns, row, strict=False))
        docs.append(_normalize_supabase_document(record))
    return docs


def _resolve_data_backend_order() -> list[str]:
    mode = app_config.resolve_data_db_mode()
    if app_config._running_on_render():
        return ["postgres"]
    if mode == "postgres":
        return ["postgres"]
    if mode == "supabase":
        return ["supabase"]
    # auto mode preference is resolved in config; keep explicit fallback chain here.
    resolved = app_config.resolve_data_db_mode()
    if resolved == "postgres":
        return ["postgres"]
    return ["supabase"]


def create_db_search_tool(  # noqa: C901
    chroma_store,
    embedding_model,
    match_threshold: float = 0.3,
    match_count: int = 5,
):
    """Create a configured db_search tool backed by Postgres/Supabase and embeddings."""
    _ = chroma_store  # Legacy arg retained for compatibility with existing callers/tests.
    embedding_cache_size = max(int(os.getenv("DB_SEARCH_EMBED_CACHE_SIZE", "256")), 0)
    embedding_cache: OrderedDict[str, list[float]] = OrderedDict()
    embedding_cache_lock = threading.Lock()

    def _update_lru_cache(key: str, value: list[float] | None = None) -> None:
        """Update cache with LRU eviction policy. Sets value if provided, moves to end."""
        if value is not None:
            embedding_cache[key] = value
        embedding_cache.move_to_end(key)
        # Evict oldest items if cache exceeds size limit
        while len(embedding_cache) > embedding_cache_size:
            embedding_cache.popitem(last=False)

    @tool
    def db_search(query: str) -> str:
        """Search the internal knowledge base for relevant information."""
        started_at = time.perf_counter()
        embedding_started_at = started_at
        retrieval_started_at = started_at
        rerank_started_at: float | None = None
        embedding_ms = 0
        retrieval_ms = 0
        rerank_ms = 0
        cache_hit = False
        retrieval_backend = "none"
        rows_before_threshold = 0
        rows_after_threshold = 0
        used_auto_inferred_tags = False

        try:
            _update_search_status("running")
            search_opts = _SEARCH_OPTIONS.get() or {}
            normalized_query = " ".join((query or "").lower().split())
            query_embedding = None
            if embedding_cache_size > 0 and normalized_query:
                with embedding_cache_lock:
                    cached_embedding = embedding_cache.get(normalized_query)
                    if cached_embedding is not None:
                        query_embedding = cached_embedding
                        cache_hit = True
                        _update_lru_cache(normalized_query)

            if query_embedding is None:
                embedding_started_at = time.perf_counter()
                query_embedding = embedding_model.embed_query(query)
                embedding_ms = int((time.perf_counter() - embedding_started_at) * 1000)
                if embedding_cache_size > 0 and normalized_query:
                    with embedding_cache_lock:
                        _update_lru_cache(normalized_query, query_embedding)

            tags = [t for t in search_opts.get("tags", []) if isinstance(t, str) and t]
            auto_infer_enabled = os.getenv("TAG_FILTER_AUTO_INFER", "true").lower() in {
                "1",
                "true",
                "yes",
            }
            auto_inferred_tags = False
            if not tags and auto_infer_enabled:
                inferred_tags = infer_tags_from_text(query, max_tags=6)
                tags = normalize_tags(inferred_tags)
                if tags:
                    auto_inferred_tags = True
                    used_auto_inferred_tags = True
                    logger.info("Auto-inferred tag filters from query: %s", tags)
            tag_mode = search_opts.get("tag_match_mode", "any")
            include_untagged_fallback = bool(search_opts.get("include_untagged_fallback", True))
            if auto_inferred_tags:
                include_untagged_fallback = False

            rows: list[dict[str, Any]] = []
            backend_order = _resolve_data_backend_order()
            for backend_name in backend_order:
                retrieval_started_at = time.perf_counter()
                if backend_name == "postgres":
                    rows = _query_postgres_fallback(
                        query_embedding=query_embedding,
                        match_threshold=float(match_threshold),
                        match_count=int(match_count),
                        tags=tags,
                        tag_mode=tag_mode,
                        include_untagged_fallback=include_untagged_fallback,
                    )
                else:
                    rows = _query_supabase_fallback(
                        query_embedding=query_embedding,
                        match_threshold=float(match_threshold),
                        match_count=int(match_count),
                        tags=tags,
                        tag_mode=tag_mode,
                        include_untagged_fallback=include_untagged_fallback,
                    )

                retrieval_ms += int((time.perf_counter() - retrieval_started_at) * 1000)
                if rows:
                    retrieval_backend = backend_name
                    break

            if not rows and tags and include_untagged_fallback:
                for backend_name in backend_order:
                    retrieval_started_at = time.perf_counter()
                    if backend_name == "postgres":
                        rows = _query_postgres_fallback(
                            query_embedding=query_embedding,
                            match_threshold=float(match_threshold),
                            match_count=int(match_count),
                            tags=[],
                            tag_mode=tag_mode,
                            include_untagged_fallback=False,
                        )
                    else:
                        rows = _query_supabase_fallback(
                            query_embedding=query_embedding,
                            match_threshold=float(match_threshold),
                            match_count=int(match_count),
                            tags=[],
                            tag_mode=tag_mode,
                            include_untagged_fallback=False,
                        )

                    retrieval_ms += int((time.perf_counter() - retrieval_started_at) * 1000)
                    if rows:
                        retrieval_backend = backend_name
                        break

            rows_before_threshold = len(rows)

            if not rows:
                _update_search_status("empty")
                _update_search_metrics(
                    {
                        "embedding_ms": embedding_ms,
                        "retrieval_ms": retrieval_ms,
                        "rerank_ms": rerank_ms,
                        "total_ms": int((time.perf_counter() - started_at) * 1000),
                        "cache_hit": cache_hit,
                        "retrieval_backend": retrieval_backend,
                        "rows_before_threshold": rows_before_threshold,
                        "rows_after_threshold": 0,
                        "auto_inferred_tags": used_auto_inferred_tags,
                        "status": "empty",
                    }
                )
                return "[]"

            filtered: list[dict[str, Any]] = []
            for row in rows:
                similarity = float(row.get("similarity", 0.0) or 0.0)
                if similarity >= float(match_threshold):
                    filtered.append(_normalize_supabase_document(row))

            if not filtered:
                _update_search_status("empty")
                _update_search_metrics(
                    {
                        "embedding_ms": embedding_ms,
                        "retrieval_ms": retrieval_ms,
                        "rerank_ms": rerank_ms,
                        "total_ms": int((time.perf_counter() - started_at) * 1000),
                        "cache_hit": cache_hit,
                        "retrieval_backend": retrieval_backend,
                        "rows_before_threshold": rows_before_threshold,
                        "rows_after_threshold": 0,
                        "auto_inferred_tags": used_auto_inferred_tags,
                        "status": "empty",
                    }
                )
                return "[]"

            rows_after_threshold = len(filtered)

            if search_opts.get("rerank"):
                rerank_started_at = time.perf_counter()
                filtered = _rerank_results(
                    query,
                    filtered,
                    int(search_opts.get("rerank_top_k", match_count)),
                )
                rerank_ms = int((time.perf_counter() - rerank_started_at) * 1000)

            _update_search_status("ok")
            _update_search_metrics(
                {
                    "embedding_ms": embedding_ms,
                    "retrieval_ms": retrieval_ms,
                    "rerank_ms": rerank_ms,
                    "total_ms": int((time.perf_counter() - started_at) * 1000),
                    "cache_hit": cache_hit,
                    "retrieval_backend": retrieval_backend,
                    "rows_before_threshold": rows_before_threshold,
                    "rows_after_threshold": rows_after_threshold,
                    "auto_inferred_tags": used_auto_inferred_tags,
                    "status": "ok",
                }
            )
            return json.dumps(filtered, ensure_ascii=False)

        except Exception as exc:
            logger.error("DB Search error: %s", exc)
            _update_search_status("error")
            _update_search_metrics(
                {
                    "embedding_ms": embedding_ms,
                    "retrieval_ms": retrieval_ms,
                    "rerank_ms": rerank_ms,
                    "total_ms": int((time.perf_counter() - started_at) * 1000),
                    "cache_hit": cache_hit,
                    "retrieval_backend": retrieval_backend,
                    "rows_before_threshold": rows_before_threshold,
                    "rows_after_threshold": rows_after_threshold,
                    "auto_inferred_tags": used_auto_inferred_tags,
                    "status": "error",
                    "error": str(exc),
                }
            )
            return "[]"

    return db_search
