"""OpenAPI example dicts for /ask-style query shapes shared by gateway and agent.

Canonical literals live here so ``apis/gateway`` does not import ``src.agent`` (T016
physical split). ``src.agent.openapi_examples`` re-exports and extends this module.
"""

from __future__ import annotations

from typing import Any

AGENT_ASK_QUESTION: dict[str, dict[str, Any]] = {
    "housing_en": {
        "summary": "English — housing programs",
        "description": "Typical answer-seeking question.",
        "value": "What affordable housing programs exist in this neighborhood?",
    },
    "health_es": {
        "summary": "Spanish — community health",
        "description": "Spanish query with regional characters.",
        "value": "¿Dónde puedo encontrar una clínica de salud comunitaria?",
    },
    "summarize_followup_en": {
        "summary": "English — contextual follow-up",
        "description": "Short follow-up that may use prior answer context.",
        "value": "Can you summarize this in 3 key points?",
    },
}

AGENT_ASK_QUERY_ALIAS: dict[str, dict[str, Any]] = {
    "legacy_query_param": {
        "summary": "Legacy ``query`` name",
        "description": "Same semantics as ``question`` when ``question`` is omitted.",
        "value": "Where is the nearest food bank?",
    },
}

AGENT_ASK_THREAD_ID: dict[str, dict[str, Any]] = {
    "default_thread": {"summary": "Default", "value": "default"},
    "client_thread": {"summary": "Client-supplied id", "value": "chat-session-7f3a"},
}

AGENT_ASK_LANG: dict[str, dict[str, Any]] = {
    "english": {"summary": "Force English", "value": "en"},
    "spanish": {"summary": "Force Spanish", "value": "es"},
}

AGENT_ASK_PROVIDER: dict[str, dict[str, Any]] = {
    "ollama": {
        "summary": "Ollama-compatible (local or Modal)",
        "value": "ollama",
    },
}

AGENT_ASK_MODEL: dict[str, dict[str, Any]] = {
    "llama31": {
        "summary": "Example model id",
        "description": "Must exist in runtime /config when overriding.",
        "value": "gemma3",
    },
}

AGENT_ASK_CONTEXT_ANSWER: dict[str, dict[str, Any]] = {
    "prior_snippet": {
        "summary": "Prior assistant answer (snippet)",
        "value": (
            "Nearby clinics include Eastside Community Health Center (walk-ins welcome) "
            "and Northside Family Medicine."
        ),
    },
}

AGENT_ASK_TAGS: dict[str, dict[str, Any]] = {
    "comma_list": {"summary": "Comma-separated tags", "value": "housing,permits"},
    "single": {"summary": "Single tag", "value": "health"},
}

AGENT_ASK_TAG_MATCH_MODE: dict[str, dict[str, Any]] = {
    "any": {"summary": "Match any listed tag", "value": "any"},
    "all": {"summary": "Require all listed tags", "value": "all"},
}

AGENT_ASK_FLAG_TRUE: dict[str, dict[str, Any]] = {
    "on": {"summary": "Enabled", "value": True},
}

AGENT_ASK_FLAG_FALSE: dict[str, dict[str, Any]] = {
    "off": {"summary": "Disabled", "value": False},
}

AGENT_ASK_RERANK_TOP_K: dict[str, dict[str, Any]] = {
    "small": {"summary": "Keep top 5 after rerank", "value": 5},
    "defaultish": {"summary": "Keep top 10", "value": 10},
}
