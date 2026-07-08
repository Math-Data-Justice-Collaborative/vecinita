"""ChatRAG backend settings (docs/config-spec.md)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from vecinita_shared_schemas.eval_config import (
    DEFAULT_EVAL_MAX_TOKENS,
    DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
    DEFAULT_EVAL_MODEL_ID,
    DEFAULT_EVAL_SYSTEM_PROMPT,
    DEFAULT_EVAL_TEMPERATURE,
    DEFAULT_EVAL_TOP_K,
)


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

    @classmethod
    def from_env(cls) -> ChatRagSettings:
        """Load settings from process environment variables."""
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            msg = "DATABASE_URL is required for ChatRAG backend"
            raise RuntimeError(msg)
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
        )
