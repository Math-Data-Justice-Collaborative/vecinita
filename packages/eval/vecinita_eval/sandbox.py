"""Apply EvalConfig sandbox overrides to eval runtime (ADR-035 §6)."""

from __future__ import annotations

from typing import Protocol

from vecinita_rag.engine import answer_without_context
from vecinita_rag.language import detect_query_language
from vecinita_rag.types import RagAnswer, RetrievedChunk

# Empirically top_k=5 x ~256-token chunks exceeded pinned vLLM max_model_len=2048
# (HTTP 500) during S017 F36 drill; top_k=2 succeeded. Cap synthesis context so
# default top_k remains usable for retrieval metrics (BUG-2026-07-31).
DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS = 3500


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


def synthesize_with_system_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    llm: CompletingLlm,
    *,
    system_prompt: str,
) -> RagAnswer:
    """Synthesize an answer using an explicit sandbox system prompt."""
    if not chunks:
        return answer_without_context(question)
    language = detect_query_language(question)
    context = truncate_synthesis_context("\n\n".join(chunk.text for chunk in chunks))
    prompt = (
        f"{system_prompt.strip()}\n\nContext:\n{context}\n\nQuestion: {question.strip()}\n\nAnswer:"
    )
    response = llm.complete(prompt)
    answer_text = getattr(response, "text", str(response))
    return RagAnswer(answer=str(answer_text), language=language, sources=chunks)
