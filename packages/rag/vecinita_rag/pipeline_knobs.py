"""Shared F42 RAG pipeline knobs and multi-query retrieve+pack (ADR-041)."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from vecinita_rag.multi_query import multi_query_retrieve
from vecinita_rag.packing import DEFAULT_CONTEXT_MAX_CHARS, PackerMode, pack_chunks
from vecinita_rag.types import RetrievedChunk

MIN_MULTI_QUERY_COUNT = 1
MAX_MULTI_QUERY_COUNT = 5
MIN_CONTEXT_MAX_CHARS = 256


@dataclass(frozen=True)
class RagPipelineKnobs:
    """Multi-query fan-out and context packing settings (F42 / config-spec)."""

    multi_query: bool
    multi_query_count: int
    packer: PackerMode
    context_max_chars: int


def _env_bool(name: str, default: bool) -> bool:  # noqa: FBT001
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def normalize_rag_pipeline_knobs(
    *,
    multi_query: bool = True,
    multi_query_count: int = 3,
    packer: PackerMode = "p3",
    context_max_chars: int = DEFAULT_CONTEXT_MAX_CHARS,
) -> RagPipelineKnobs:
    """Clamp F42 knobs to config-spec bounds."""
    count = max(MIN_MULTI_QUERY_COUNT, min(MAX_MULTI_QUERY_COUNT, multi_query_count))
    packer_mode: PackerMode = "p3" if packer == "p3" else "p1"
    max_chars = max(MIN_CONTEXT_MAX_CHARS, context_max_chars)
    return RagPipelineKnobs(
        multi_query=multi_query,
        multi_query_count=count,
        packer=packer_mode,
        context_max_chars=max_chars,
    )


def rag_pipeline_knobs_from_env() -> RagPipelineKnobs:
    """Read ``VECINITA_RAG_*`` env vars shared by ChatRAG and eval (ADR-041)."""
    count_raw = os.environ.get("VECINITA_RAG_MULTI_QUERY_COUNT", "3")
    try:
        count = int(count_raw)
    except ValueError:
        count = 3
    packer_raw = os.environ.get("VECINITA_RAG_PACKER", "p3").strip().lower()
    packer: PackerMode = "p3" if packer_raw == "p3" else "p1"
    max_chars_raw = os.environ.get(
        "VECINITA_RAG_CONTEXT_MAX_CHARS",
        str(DEFAULT_CONTEXT_MAX_CHARS),
    )
    try:
        max_chars = int(max_chars_raw)
    except ValueError:
        max_chars = DEFAULT_CONTEXT_MAX_CHARS
    return normalize_rag_pipeline_knobs(
        multi_query=_env_bool("VECINITA_RAG_MULTI_QUERY", default=True),
        multi_query_count=count,
        packer=packer,
        context_max_chars=max_chars,
    )


def retrieve_multi_query_packed(
    question: str,
    *,
    locale: str,
    top_k: int,
    retrieve_fn: Callable[[str], list[RetrievedChunk]],
    knobs: RagPipelineKnobs,
) -> tuple[list[RetrievedChunk], str]:
    """Run multi-query retrieval and pack context with shared F42 knobs."""
    chunks = multi_query_retrieve(
        question,
        locale=locale,
        top_k=top_k,
        retrieve_fn=retrieve_fn,
        enabled=knobs.multi_query,
        count=knobs.multi_query_count,
    )
    context = pack_chunks(chunks, mode=knobs.packer, max_chars=knobs.context_max_chars)
    return chunks, context
