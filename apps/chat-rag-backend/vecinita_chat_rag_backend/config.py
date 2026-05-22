"""ChatRAG backend settings (docs/config-spec.md)."""

from __future__ import annotations

import os
from dataclasses import dataclass


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

    @classmethod
    def from_env(cls) -> ChatRagSettings:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required for ChatRAG backend")
        return cls(
            database_url=_normalize_database_url(database_url),
            top_k=_int_env("VECINITA_TOP_K", 5),
            min_retrieval_score=_float_env("VECINITA_MIN_RETRIEVAL_SCORE", 0.2),
            chat_max_tokens=_int_env("VECINITA_CHAT_MAX_TOKENS", 256),
            embed_url=os.environ.get("VECINITA_MODAL_EMBED_URL"),
            llm_url=os.environ.get("VECINITA_MODAL_LLM_URL"),
            request_timeout_s=float(os.environ.get("VECINITA_REQUEST_TIMEOUT_S", "120")),
        )
