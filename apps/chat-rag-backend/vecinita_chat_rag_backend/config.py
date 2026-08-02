"""ChatRAG backend settings (docs/config-spec.md)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from vecinita_rag.cache import (
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_CACHE_TTL_S,
    DEFAULT_SEMANTIC_THRESHOLD,
)
from vecinita_rag.packing import DEFAULT_CONTEXT_MAX_CHARS, PackerMode
from vecinita_shared_schemas.eval_config import (
    DEFAULT_EVAL_MAX_TOKENS,
    DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
    DEFAULT_EVAL_MODEL_ID,
    DEFAULT_EVAL_SYSTEM_PROMPT,
    DEFAULT_EVAL_TEMPERATURE,
    DEFAULT_EVAL_TOP_K,
)

_MIN_MULTI_QUERY_COUNT = 1
_MAX_MULTI_QUERY_COUNT = 5
_MIN_CONTEXT_MAX_CHARS = 256
_MIN_CACHE_TTL_S = 60
_MAX_CACHE_TTL_S = 86400
_MIN_CACHE_MAX_ENTRIES = 16
_MAX_CACHE_MAX_ENTRIES = 100000
_MIN_CACHE_SEMANTIC_THRESHOLD = 0.5
_MAX_CACHE_SEMANTIC_THRESHOLD = 1.0


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return float(raw)


def _str_env(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw


def _bool_env(name: str, default: bool) -> bool:  # noqa: FBT001  # internal helper mirrors _int_env/_float_env positional default style
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _rag_packer_env(name: str, default: PackerMode) -> PackerMode:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value == "p1":
        return "p1"
    if value == "p3":
        return "p3"
    msg = f"{name} must be 'p1' or 'p3' (got {raw!r})"
    raise ValueError(msg)


def _validate_f42_rag_knobs(
    *,
    rag_multi_query_count: int,
    rag_packer: PackerMode,
    rag_context_max_chars: int,
) -> None:
    if not (_MIN_MULTI_QUERY_COUNT <= rag_multi_query_count <= _MAX_MULTI_QUERY_COUNT):
        msg = (
            "VECINITA_RAG_MULTI_QUERY_COUNT must be between "
            f"{_MIN_MULTI_QUERY_COUNT} and {_MAX_MULTI_QUERY_COUNT}"
        )
        raise ValueError(msg)
    if rag_packer not in ("p1", "p3"):
        msg = f"VECINITA_RAG_PACKER must be 'p1' or 'p3' (got {rag_packer!r})"
        raise ValueError(msg)
    if rag_context_max_chars < _MIN_CONTEXT_MAX_CHARS:
        msg = f"VECINITA_RAG_CONTEXT_MAX_CHARS must be >= {_MIN_CONTEXT_MAX_CHARS}"
        raise ValueError(msg)


def _validate_f43_rag_cache_knobs(
    *,
    rag_cache_ttl_s: int,
    rag_cache_max_entries: int,
    rag_cache_semantic_threshold: float,
) -> None:
    if not (_MIN_CACHE_TTL_S <= rag_cache_ttl_s <= _MAX_CACHE_TTL_S):
        msg = (
            "VECINITA_RAG_CACHE_TTL_S must be between "
            f"{_MIN_CACHE_TTL_S} and {_MAX_CACHE_TTL_S}"
        )
        raise ValueError(msg)
    if not (_MIN_CACHE_MAX_ENTRIES <= rag_cache_max_entries <= _MAX_CACHE_MAX_ENTRIES):
        msg = (
            "VECINITA_RAG_CACHE_MAX_ENTRIES must be between "
            f"{_MIN_CACHE_MAX_ENTRIES} and {_MAX_CACHE_MAX_ENTRIES}"
        )
        raise ValueError(msg)
    if not (
        _MIN_CACHE_SEMANTIC_THRESHOLD
        <= rag_cache_semantic_threshold
        <= _MAX_CACHE_SEMANTIC_THRESHOLD
    ):
        msg = (
            "VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD must be between "
            f"{_MIN_CACHE_SEMANTIC_THRESHOLD} and {_MAX_CACHE_SEMANTIC_THRESHOLD}"
        )
        raise ValueError(msg)


@dataclass(frozen=True)
class ChatRagSettings:
    """Runtime settings for retrieval, embedding, and LLM upstreams."""

    database_url: str
    top_k: int
    embed_url: str | None
    llm_url: str | None
    request_timeout_s: float
    min_retrieval_score: float = 0.2
    chat_max_tokens: int = 256
    browse_page_size: int = 20
    internal_write_url: str | None = None
    internal_api_key: str | None = None
    stats_enabled: bool = True
    llm_model_id: str | None = None
    fallback_top_k: int = DEFAULT_EVAL_TOP_K
    fallback_min_retrieval_score: float = DEFAULT_EVAL_MIN_RETRIEVAL_SCORE
    fallback_system_prompt: str = DEFAULT_EVAL_SYSTEM_PROMPT
    fallback_max_tokens: int = DEFAULT_EVAL_MAX_TOKENS
    fallback_temperature: float = DEFAULT_EVAL_TEMPERATURE
    fallback_model_id: str = DEFAULT_EVAL_MODEL_ID
    rag_multi_query: bool = True
    rag_multi_query_count: int = 3
    rag_packer: PackerMode = "p1"
    rag_context_max_chars: int = DEFAULT_CONTEXT_MAX_CHARS
    rag_cache: bool = True
    rag_cache_ttl_s: int = DEFAULT_CACHE_TTL_S
    rag_cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES
    rag_cache_semantic: bool = True
    rag_cache_semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD

    @classmethod
    def from_env(cls) -> ChatRagSettings:
        """Load settings from process environment variables."""
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            msg = "DATABASE_URL is required for ChatRAG backend"
            raise RuntimeError(msg)
        rag_multi_query_count = _int_env("VECINITA_RAG_MULTI_QUERY_COUNT", 3)
        rag_packer: PackerMode = _rag_packer_env("VECINITA_RAG_PACKER", "p1")
        rag_context_max_chars = _int_env(
            "VECINITA_RAG_CONTEXT_MAX_CHARS",
            DEFAULT_CONTEXT_MAX_CHARS,
        )
        _validate_f42_rag_knobs(
            rag_multi_query_count=rag_multi_query_count,
            rag_packer=rag_packer,
            rag_context_max_chars=rag_context_max_chars,
        )
        rag_cache_ttl_s = _int_env("VECINITA_RAG_CACHE_TTL_S", DEFAULT_CACHE_TTL_S)
        rag_cache_max_entries = _int_env(
            "VECINITA_RAG_CACHE_MAX_ENTRIES",
            DEFAULT_CACHE_MAX_ENTRIES,
        )
        rag_cache_semantic_threshold = _float_env(
            "VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD",
            DEFAULT_SEMANTIC_THRESHOLD,
        )
        _validate_f43_rag_cache_knobs(
            rag_cache_ttl_s=rag_cache_ttl_s,
            rag_cache_max_entries=rag_cache_max_entries,
            rag_cache_semantic_threshold=rag_cache_semantic_threshold,
        )
        return cls(
            database_url=_normalize_database_url(database_url),
            top_k=_int_env("VECINITA_TOP_K", 5),
            min_retrieval_score=_float_env("VECINITA_MIN_RETRIEVAL_SCORE", 0.2),
            chat_max_tokens=_int_env("VECINITA_CHAT_MAX_TOKENS", 256),
            browse_page_size=_int_env("VECINITA_BROWSE_PAGE_SIZE", 20),
            embed_url=os.environ.get("VECINITA_MODAL_EMBED_URL"),
            llm_url=os.environ.get("VECINITA_MODAL_LLM_URL"),
            request_timeout_s=float(os.environ.get("VECINITA_REQUEST_TIMEOUT_S", "120")),
            internal_write_url=os.environ.get("VECINITA_INTERNAL_WRITE_URL"),
            internal_api_key=os.environ.get("VECINITA_INTERNAL_API_KEY"),
            stats_enabled=_bool_env("VECINITA_STATS_ENABLED", default=True),
            llm_model_id=os.environ.get("VECINITA_LLM_MODEL_ID")
            or os.environ.get("VECINITA_OLLAMA_MODEL_ID", DEFAULT_EVAL_MODEL_ID),
            fallback_top_k=_int_env("VECINITA_RAG_CONFIG_FALLBACK_TOP_K", DEFAULT_EVAL_TOP_K),
            fallback_min_retrieval_score=_float_env(
                "VECINITA_RAG_CONFIG_FALLBACK_MIN_RETRIEVAL_SCORE",
                DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
            ),
            fallback_system_prompt=_str_env(
                "VECINITA_RAG_CONFIG_FALLBACK_SYSTEM_PROMPT",
                DEFAULT_EVAL_SYSTEM_PROMPT,
            ),
            fallback_max_tokens=_int_env(
                "VECINITA_RAG_CONFIG_FALLBACK_MAX_TOKENS",
                DEFAULT_EVAL_MAX_TOKENS,
            ),
            fallback_temperature=_float_env(
                "VECINITA_RAG_CONFIG_FALLBACK_TEMPERATURE",
                DEFAULT_EVAL_TEMPERATURE,
            ),
            fallback_model_id=os.environ.get(
                "VECINITA_RAG_CONFIG_FALLBACK_MODEL_ID",
                DEFAULT_EVAL_MODEL_ID,
            ),
            rag_multi_query=_bool_env("VECINITA_RAG_MULTI_QUERY", default=True),
            rag_multi_query_count=rag_multi_query_count,
            rag_packer=rag_packer,
            rag_context_max_chars=rag_context_max_chars,
            rag_cache=_bool_env("VECINITA_RAG_CACHE", default=True),
            rag_cache_ttl_s=rag_cache_ttl_s,
            rag_cache_max_entries=rag_cache_max_entries,
            rag_cache_semantic=_bool_env("VECINITA_RAG_CACHE_SEMANTIC", default=True),
            rag_cache_semantic_threshold=rag_cache_semantic_threshold,
        )
