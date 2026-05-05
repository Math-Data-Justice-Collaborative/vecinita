"""Gateway OpenAPI example dicts and stable sample values for public routers.

Ask-related examples come from ``src.gateway_openapi_ask_examples`` so the gateway
tree does not depend on ``src.agent`` after the apis/agent vs apis/gateway split.
"""

from __future__ import annotations

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

from .models import DOCUMENTS_DEFAULT_SOURCE_URL

__all__ = [
    "AGENT_ASK_CONTEXT_ANSWER",
    "AGENT_ASK_FLAG_FALSE",
    "AGENT_ASK_FLAG_TRUE",
    "AGENT_ASK_LANG",
    "AGENT_ASK_MODEL",
    "AGENT_ASK_PROVIDER",
    "AGENT_ASK_QUESTION",
    "AGENT_ASK_QUERY_ALIAS",
    "AGENT_ASK_RERANK_TOP_K",
    "AGENT_ASK_TAG_MATCH_MODE",
    "AGENT_ASK_TAGS",
    "AGENT_ASK_THREAD_ID",
    "DOCUMENTS_DEFAULT_SOURCE_URL",
]
