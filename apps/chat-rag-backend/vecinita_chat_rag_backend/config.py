"""ChatRAG backend settings (docs/config-spec.md)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return int(raw)


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@dataclass(frozen=True)
class ChatRagSettings:
    database_url: str
    top_k: int
    embed_url: str | None
    llm_url: str | None
    request_timeout_s: float

    @classmethod
    def from_env(cls) -> ChatRagSettings:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required for ChatRAG backend")
        return cls(
            database_url=_normalize_database_url(database_url),
            top_k=_int_env("VECINITA_TOP_K", 5),
            embed_url=os.environ.get("VECINITA_MODAL_EMBED_URL"),
            llm_url=os.environ.get("VECINITA_MODAL_LLM_URL"),
            request_timeout_s=float(os.environ.get("VECINITA_REQUEST_TIMEOUT_S", "60")),
        )
