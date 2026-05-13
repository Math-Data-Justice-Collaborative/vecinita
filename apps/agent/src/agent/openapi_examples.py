"""OpenAPI ``openapi_examples`` for agent routes (Schemathesis explicit phase, Swagger UI).

See https://schemathesis.readthedocs.io/en/stable/examples.html
Shared /ask query shapes live in ``src.gateway_openapi_ask_examples`` (gateway/agent split).
"""

from __future__ import annotations

from typing import Any

from src.gateway_openapi_ask_examples import (
    AGENT_ASK_CONTEXT_ANSWER,
    AGENT_ASK_FLAG_FALSE,
    AGENT_ASK_FLAG_TRUE,
    AGENT_ASK_LANG,
    AGENT_ASK_MODEL,
    AGENT_ASK_PROVIDER,
    AGENT_ASK_QUERY_ALIAS,
    AGENT_ASK_QUESTION,
    AGENT_ASK_RERANK_TOP_K,
    AGENT_ASK_TAG_MATCH_MODE,
    AGENT_ASK_TAGS,
    AGENT_ASK_THREAD_ID,
)

AGENT_ASK_CLARIFICATION_RESPONSE: dict[str, dict[str, Any]] = {
    "clarify_yes": {
        "summary": "User reply to clarification",
        "value": "I meant housing resources in ZIP 94110.",
    },
}

# --- GET /test-db-search ---

AGENT_TEST_DB_SEARCH_QUERY: dict[str, dict[str, Any]] = {
    "community": {
        "summary": "Community resources",
        "value": "community resources",
    },
    "housing": {
        "summary": "Housing-related",
        "value": "affordable housing intake",
    },
}

# --- POST /model-selection (request body) ---

AGENT_MODEL_SELECTION_BODY: dict[str, dict[str, Any]] = {
    "keep_defaults": {
        "summary": "Keep current model (explicit ollama)",
        "value": {"provider": "ollama", "model": None, "lock": False},
    },
    "set_model_unlocked": {
        "summary": "Select a model (must exist in /config)",
        "value": {"provider": "ollama", "model": "gemma3", "lock": False},
    },
    "lock_selection": {
        "summary": "Lock selection",
        "value": {"provider": "ollama", "model": "gemma3", "lock": True},
    },
    "lock_without_model": {
        "summary": "Lock policy without changing the active model tag",
        "value": {"provider": "ollama", "model": None, "lock": True},
    },
    "alternate_tag": {
        "summary": "Pin a different local tag when available",
        "value": {"provider": "ollama", "model": "llama3.1:70b", "lock": False},
    },
}

__all__ = [
    "AGENT_ASK_CONTEXT_ANSWER",
    "AGENT_ASK_FLAG_FALSE",
    "AGENT_ASK_FLAG_TRUE",
    "AGENT_ASK_LANG",
    "AGENT_ASK_MODEL",
    "AGENT_ASK_PROVIDER",
    "AGENT_ASK_QUERY_ALIAS",
    "AGENT_ASK_QUESTION",
    "AGENT_ASK_RERANK_TOP_K",
    "AGENT_ASK_TAG_MATCH_MODE",
    "AGENT_ASK_TAGS",
    "AGENT_ASK_THREAD_ID",
    "AGENT_ASK_CLARIFICATION_RESPONSE",
    "AGENT_TEST_DB_SEARCH_QUERY",
    "AGENT_MODEL_SELECTION_BODY",
]
