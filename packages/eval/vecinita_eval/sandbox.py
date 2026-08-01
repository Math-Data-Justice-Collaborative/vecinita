"""Apply EvalConfig sandbox overrides to eval runtime (ADR-035 §6, F42 ADR-041)."""

from __future__ import annotations

from typing import Protocol

from vecinita_rag.engine import answer_without_context
from vecinita_rag.language import detect_query_language
from vecinita_rag.packing import DEFAULT_CONTEXT_MAX_CHARS, PackerMode, pack_chunks
from vecinita_rag.types import RagAnswer, RetrievedChunk

# Empirically top_k=5 x ~256-token chunks exceeded pinned vLLM max_model_len=2048
# (HTTP 500) during S017 F36 drill; top_k=2 succeeded. Cap synthesis context so
# default top_k remains usable for retrieval metrics (BUG-2026-07-31).
DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS = DEFAULT_CONTEXT_MAX_CHARS


class CompletingLlm(Protocol):
    """Minimal LLM surface used by sandbox synthesis (matches judge contract)."""

    def complete(self, prompt: str) -> object:
        """Return a completion object (often with a ``text`` attribute)."""
        ...


def truncate_synthesis_context(
    context: str,
    *,
    max_chars: int = DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS,
) -> str:
    """Return ``context`` capped to ``max_chars`` (prefix) for RAG synthesis prompts."""
    if max_chars < 1:
        msg = "max_chars must be >= 1"
        raise ValueError(msg)
    if len(context) <= max_chars:
        return context
    return context[:max_chars]


def synthesize_with_system_prompt(  # noqa: PLR0913 — sandbox needs question/chunks/llm + F42 packer knobs
    question: str,
    chunks: list[RetrievedChunk],
    llm: CompletingLlm,
    *,
    system_prompt: str,
    packer: PackerMode = "p1",
    context_max_chars: int = DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS,
) -> RagAnswer:
    """Synthesize an answer using an explicit sandbox system prompt (shared F42 packer)."""
    if not chunks:
        return answer_without_context(question)
    language = detect_query_language(question)
    # P1/P3 pack via packages/rag; always prefix-cap for vLLM max_model_len safety.
    packed = pack_chunks(chunks, mode=packer, max_chars=context_max_chars)
    context = truncate_synthesis_context(packed, max_chars=context_max_chars)
    prompt = (
        f"{system_prompt.strip()}\n\nContext:\n{context}\n\nQuestion: {question.strip()}\n\nAnswer:"
    )
    response = llm.complete(prompt)
    answer_text = getattr(response, "text", str(response))
    return RagAnswer(answer=str(answer_text), language=language, sources=chunks)
