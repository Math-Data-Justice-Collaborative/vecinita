"""Compatibility layer for legacy services import paths.

Canonical implementation lives in src.agent.tools.db_search. This module keeps
older imports functional while using the Postgres-only search path.
"""

import logging
import os
from typing import Any, cast

from langchain_core.tools import tool

from src.agent.tools.db_search import create_db_search_tool as _create_db_search_tool
from src.agent.tools.db_search import get_last_search_metrics, get_last_search_status
from src.agent.tools.db_search import reset_search_options, set_search_options

logger = logging.getLogger(__name__)
_DEFAULT_DB_SEARCH = None


def create_db_search_tool(
    store_client,
    embedding_model,
    match_threshold: float = 0.3,
    match_count: int = 5,
    session_id: str | None = None,
):
    _ = session_id
    return _create_db_search_tool(
        store_client,
        embedding_model,
        match_threshold=match_threshold,
        match_count=match_count,
    )


@tool
def db_search_tool(query: str) -> str:
    """Search the internal knowledge base for relevant information."""
    global _DEFAULT_DB_SEARCH
    if _DEFAULT_DB_SEARCH is None:
        embedding_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
            _DEFAULT_DB_SEARCH = _create_db_search_tool(
                store_client=None,
                embedding_model=embedding_model,
                match_threshold=float(os.getenv("DB_MATCH_THRESHOLD", "0.3")),
                match_count=int(os.getenv("DB_MATCH_COUNT", "5")),
            )
        except Exception as exc:
            logger.error("Failed to initialize db_search_tool: %s", exc)
            return "[]"

    try:
        return cast(str, _DEFAULT_DB_SEARCH.invoke(query))
    except Exception as exc:
        logger.error("db_search_tool runtime error: %s", exc)
        return "[]"
