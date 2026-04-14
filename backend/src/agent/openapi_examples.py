"""OpenAPI ``openapi_examples`` for agent routes (Schemathesis explicit phase, Swagger UI).

See https://schemathesis.readthedocs.io/en/stable/examples.html
"""

from __future__ import annotations

from typing import Any

# --- GET /ask and GET /ask/stream (shared query shapes) ---

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
