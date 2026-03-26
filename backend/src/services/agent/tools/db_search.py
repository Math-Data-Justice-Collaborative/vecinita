"""Database search tool for Vecinita agent.

This tool performs vector similarity search against the Supabase database
to retrieve relevant document chunks for answering user questions.
"""

import json
import logging
import os
import re
from contextvars import ContextVar, Token
from typing import Any, cast

from langchain_core.tools import tool
from supabase import create_client

logger = logging.getLogger(__name__)

_DEFAULT_DB_SEARCH = None

_SEARCH_OPTIONS: ContextVar[dict[str, Any] | None] = ContextVar(
    "services_db_search_options",
    default=None,
)


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


def _normalize_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Normalize document field names from Supabase response.

    Different Supabase schemas may use different field names.
    This function provides fallback logic to handle variations.

    Args:
        doc: Raw document dictionary from Supabase

    Returns:
        Normalized document with 'content', 'source_url', 'similarity', and position fields
    """
    source = doc.get("source_url") or doc.get("source") or doc.get("url") or "Unknown source"
    content = doc.get("content") or doc.get("text") or doc.get("chunk_text") or ""
    similarity = doc.get("similarity", 0.0)
    chunk_index = doc.get("chunk_index")
    total_chunks = doc.get("total_chunks")
    metadata = doc.get("metadata", {})

    # Extract position info from metadata if available
    # Always include these fields for consistent return type
    result = {
        "content": content,
        "source_url": source,
        "similarity": similarity,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "char_start": None,
        "char_end": None,
        "doc_index": None,
        "metadata": metadata,  # Include full metadata for frontend use
    }

    # Populate position fields from metadata if available
    if isinstance(metadata, dict):
        result["char_start"] = metadata.get("char_start")
        result["char_end"] = metadata.get("char_end")
        result["doc_index"] = metadata.get("doc_index")

    return result


def _format_db_error(e: Exception) -> str:
    """Return a human-friendly message describing common DB search failures.

    Tries to distinguish typical issues to aid debugging: missing RPC,
    connectivity problems, auth failures, and embedding dimension mismatches.
    """
    msg = str(e).lower()

    # Function overloading conflict (PGRST203)
    if (
        "pgrst203" in msg
        or "could not choose the best candidate function" in msg
        or "function overloading" in msg
    ):
        return (
            "RPC function overload conflict: Multiple versions of 'search_similar_documents' exist. "
            "Run scripts/fix_rpc_overload.sql in Supabase SQL Editor to resolve."
        )

    # RPC function missing
    if "search_similar_documents" in msg and ("not found" in msg or "does not exist" in msg):
        return (
            "RPC function not found: 'search_similar_documents'. "
            "Ensure schema is installed (see scripts/schema_install.sql)."
        )

    # Connectivity / timeout
    if "connection" in msg or "timeout" in msg or "failed to establish" in msg or "network" in msg:
        return "Database connection error. Check network access and SUPABASE_URL."

    # Authentication
    if "unauthorized" in msg or "invalid api key" in msg or "401" in msg:
        return "Supabase authentication failed. Verify SUPABASE_KEY and permissions."

    # Embedding / pgvector dimension mismatch
    if "dimension" in msg or "array length" in msg or "pgvector" in msg:
        return "Embedding dimension mismatch. Ensure model and pgvector column match (e.g., 384)."

    return "Unexpected database error"


@tool
def db_search_tool(query: str) -> str:
    """Search the internal knowledge base for relevant information.

    Use this tool to find information from the Vecinita document database.
    It performs vector similarity search to retrieve the most relevant content
    for answering the user's question.

    Args:
        query: The user's question or search query

    Returns:
        A JSON string containing a list of relevant documents. Parse the result
        with json.loads() to get Python objects. Each document contains 'content',
        'source_url', 'similarity', and position fields. Returns "[]" (empty JSON array)
        if no relevant documents are found.

    Example:
        >>> results = db_search_tool("What community services are available?")
        >>> import json
        >>> docs = json.loads(results)  # Parse JSON string to Python list
        >>> for doc in docs:
        ...     print(f"Source: {doc['source_url']}")
        ...     print(f"Content: {doc['content']}")
    """
    global _DEFAULT_DB_SEARCH

    if _DEFAULT_DB_SEARCH is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        embedding_model_name = os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )

        if not supabase_url or not supabase_key:
            logger.warning("db_search_tool not configured: missing SUPABASE_URL or SUPABASE_KEY")
            return "[]"

        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            supabase_client = create_client(supabase_url, supabase_key)
            embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
            _DEFAULT_DB_SEARCH = create_db_search_tool(
                supabase_client,
                embedding_model,
                match_threshold=float(os.getenv("DB_MATCH_THRESHOLD", "0.3")),
                match_count=int(os.getenv("DB_MATCH_COUNT", "5")),
                session_id=None,
            )
        except Exception as exc:
            logger.error("Failed to initialize db_search_tool: %s", exc)
            return "[]"

    try:
        return cast(str, _DEFAULT_DB_SEARCH.invoke({"query": query}))
    except Exception as exc:
        logger.error("db_search_tool runtime error: %s", exc)
        return "[]"


def create_db_search_tool(
    supabase_client,
    embedding_model,
    match_threshold: float = 0.3,
    match_count: int = 5,
    session_id: str | None = None,
):
    """Create a configured db_search tool with access to Supabase and embeddings.

    Args:
        supabase_client: Initialized Supabase client
        embedding_model: Initialized embedding model (HuggingFaceEmbeddings)
        match_threshold: Minimum similarity threshold (default: 0.3)
        match_count: Maximum number of results to return (default: 5)
        session_id: Optional session ID for data isolation (default: None = public data only)

    Returns:
        A configured tool function that can be used with LangGraph
    """

    @tool
    def db_search(query: str) -> str:
        """Search the internal knowledge base for relevant information.

        Use this tool to find information from the Vecinita document database.
        It performs vector similarity search to retrieve the most relevant content
        for answering the user's question.

        Args:
            query: The user's question or search query

        Returns:
            A JSON string containing a list of relevant documents. Parse the result
            with json.loads() to get Python objects. Returns "[]" (empty JSON array)
            if no relevant documents are found or on error.
        """
        try:
            logger.info(f"DB Search: Generating embedding for query: '{query}'")
            question_embedding = embedding_model.embed_query(query)
            logger.info(f"DB Search: Embedding generated. Dimension: {len(question_embedding)}")
            logger.info(f"DB Search: Embedding first 5 values: {question_embedding[:5]}")

            logger.info(
                f"DB Search: Searching Supabase with threshold={match_threshold}, match_count={match_count}, session_id={session_id}..."
            )

            # Prepare RPC parameters
            search_opts = _SEARCH_OPTIONS.get() or {}
            rpc_params = {
                "query_embedding": question_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
            }

            if search_opts.get("tags"):
                rpc_params.update(
                    {
                        "tag_filter": search_opts.get("tags", []),
                        "tag_match_mode": search_opts.get("tag_match_mode", "any"),
                        "include_untagged_fallback": search_opts.get(
                            "include_untagged_fallback", True
                        ),
                    }
                )

            # Add session_filter if session_id is provided
            if session_id:
                rpc_params["session_filter"] = session_id
                logger.info(f"DB Search: Using session filter: {session_id}")
            else:
                logger.info("DB Search: No session filter - searching public data only")

            try:
                relevant_docs = supabase_client.rpc(
                    "search_similar_documents", rpc_params
                ).execute()
            except Exception as rpc_error:
                if "tag_filter" in rpc_params and any(
                    marker in str(rpc_error).lower()
                    for marker in ["does not exist", "could not find", "unexpected", "signature"]
                ):
                    logger.warning(
                        "DB Search: Falling back to legacy RPC signature without tag filters"
                    )
                    fallback_params = {
                        "query_embedding": question_embedding,
                        "match_threshold": match_threshold,
                        "match_count": match_count,
                    }
                    if session_id:
                        fallback_params["session_filter"] = session_id
                    relevant_docs = supabase_client.rpc(
                        "search_similar_documents",
                        fallback_params,
                    ).execute()
                else:
                    raise

            logger.info(f"DB Search: RPC call completed. Result type: {type(relevant_docs)}")
            logger.info(
                f"DB Search: Found {len(relevant_docs.data) if relevant_docs.data else 0} relevant documents"
            )

            if relevant_docs.data:
                # Log similarity scores for debugging
                similarities = [doc.get("similarity", 0) for doc in relevant_docs.data]
                logger.info(f"DB Search: Similarity scores: {similarities}")
                logger.info(
                    f"DB Search: Min={min(similarities):.3f}, Max={max(similarities):.3f}, Avg={sum(similarities) / len(similarities):.3f}"
                )

            if not relevant_docs.data:
                # Return empty JSON array string when no relevant documents are found
                logger.warning(
                    f"DB Search: No documents found with threshold {match_threshold}. Consider lowering threshold."
                )
                return "[]"

            # Normalize document format using helper function
            results = [_normalize_document(doc) for doc in relevant_docs.data]

            if search_opts.get("rerank"):
                results = _rerank_results(
                    query,
                    results,
                    int(search_opts.get("rerank_top_k", match_count)),
                )

            # Return JSON string for proper LLM serialization
            logger.info(f"DB Search: Returning {len(results)} results as JSON")
            return json.dumps(results, ensure_ascii=False)

        except Exception as e:
            logger.error(f"DB Search: {_format_db_error(e)}: {e}")
            # Return empty JSON array string on error to keep agent robust and satisfy tests
            return "[]"

    return db_search
