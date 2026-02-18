"""Database search tool for Vecinita agent.

This tool performs vector similarity search against the Supabase database
to retrieve relevant document chunks for answering user questions.
"""

import logging
from typing import List, Dict, Any
import json
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _normalize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize document field names from Supabase response.

    Different Supabase schemas may use different field names.
    This function provides fallback logic to handle variations.

    Args:
        doc: Raw document dictionary from Supabase

    Returns:
        Normalized document with 'content', 'source_url', 'similarity', and position fields
    """
    source = (
        doc.get('source_url')
        or doc.get('source')
        or doc.get('url')
        or 'Unknown source'
    )
    content = (
        doc.get('content')
        or doc.get('text')
        or doc.get('chunk_text')
        or ''
    )
    similarity = doc.get('similarity', 0.0)
    chunk_index = doc.get('chunk_index')
    total_chunks = doc.get('total_chunks')
    metadata = doc.get('metadata', {})

    # Extract position info from metadata if available
    # Always include these fields for consistent return type
    result = {
        'content': content,
        'source_url': source,
        'similarity': similarity,
        'chunk_index': chunk_index,
        'total_chunks': total_chunks,
        'char_start': None,
        'char_end': None,
        'doc_index': None,
        'metadata': metadata,  # Include full metadata for frontend use
    }

    # Populate position fields from metadata if available
    if isinstance(metadata, dict):
        result['char_start'] = metadata.get('char_start')
        result['char_end'] = metadata.get('char_end')
        result['doc_index'] = metadata.get('doc_index')

    return result


def _format_db_error(e: Exception) -> str:
    """Return a human-friendly message describing common DB search failures.

    Tries to distinguish typical issues to aid debugging: missing RPC,
    connectivity problems, auth failures, and embedding dimension mismatches.
    """
    msg = str(e).lower()

    # Function overloading conflict (PGRST203)
    if (
        "pgrst203" in msg or
        "could not choose the best candidate function" in msg or
        "function overloading" in msg
    ):
        return (
            "RPC function overload conflict: Multiple versions of 'search_similar_documents' exist. "
            "Run scripts/fix_rpc_overload.sql in Supabase SQL Editor to resolve."
        )

    # RPC function missing
    if (
        "search_similar_documents" in msg and
        ("not found" in msg or "does not exist" in msg)
    ):
        return (
            "RPC function not found: 'search_similar_documents'. "
            "Ensure schema is installed (see scripts/schema_install.sql)."
        )

    # Connectivity / timeout
    if (
        "connection" in msg or
        "timeout" in msg or
        "failed to establish" in msg or
        "network" in msg
    ):
        return (
            "Database connection error. Check network access and SUPABASE_URL."
        )

    # Authentication
    if (
        "unauthorized" in msg or
        "invalid api key" in msg or
        "401" in msg
    ):
        return (
            "Supabase authentication failed. Verify SUPABASE_KEY and permissions."
        )

    # Embedding / pgvector dimension mismatch
    if (
        "dimension" in msg or
        "array length" in msg or
        "pgvector" in msg
    ):
        return (
            "Embedding dimension mismatch. Ensure model and pgvector column match (e.g., 384)."
        )

    return "Unexpected database error"


def create_db_search_tool(supabase_client, embedding_model, match_threshold: float = 0.3, match_count: int = 5):
    """Create a configured db_search tool with access to Supabase and embeddings.

    Args:
        supabase_client: Initialized Supabase client
        embedding_model: Initialized embedding model (HuggingFaceEmbeddings)
        match_threshold: Minimum similarity threshold (default: 0.3)
        match_count: Maximum number of results to return (default: 5)

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
            logger.info(
                f"DB Search: Generating embedding for query: '{query}'")
            question_embedding = embedding_model.embed_query(query)
            logger.info(
                f"DB Search: Embedding generated. Dimension: {len(question_embedding)}")
            logger.info(
                f"DB Search: Embedding first 5 values: {question_embedding[:5]}")

            logger.info(
                f"DB Search: Searching Supabase with threshold={match_threshold}, match_count={match_count}...")
            relevant_docs = supabase_client.rpc(
                "search_similar_documents",
                {
                    "query_embedding": question_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count
                },
            ).execute()

            logger.info(
                f"DB Search: RPC call completed. Result type: {type(relevant_docs)}")
            logger.info(
                f"DB Search: Found {len(relevant_docs.data) if relevant_docs.data else 0} relevant documents")

            if relevant_docs.data:
                # Log similarity scores for debugging
                similarities = [doc.get('similarity', 0)
                                for doc in relevant_docs.data]
                logger.info(f"DB Search: Similarity scores: {similarities}")
                logger.info(
                    f"DB Search: Min={min(similarities):.3f}, Max={max(similarities):.3f}, Avg={sum(similarities)/len(similarities):.3f}")

            if not relevant_docs.data:
                # Return empty JSON array string when no relevant documents are found
                logger.warning(
                    f"DB Search: No documents found with threshold {match_threshold}. Consider lowering threshold.")
                return "[]"

            # Normalize document format using helper function
            results = [_normalize_document(doc) for doc in relevant_docs.data]

            # Return JSON string for proper LLM serialization
            logger.info(f"DB Search: Returning {len(results)} results as JSON")
            return json.dumps(results, ensure_ascii=False)

        except Exception as e:
            logger.error(f"DB Search: {_format_db_error(e)}: {e}")
            # Return empty JSON array string on error to keep agent robust and satisfy tests
            return "[]"

    return db_search
