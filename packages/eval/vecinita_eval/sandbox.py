"""Apply EvalConfig sandbox overrides to eval runtime (ADR-035 §6)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vecinita_rag.engine import answer_without_context
from vecinita_rag.language import detect_query_language
from vecinita_rag.types import RagAnswer, RetrievedChunk

if TYPE_CHECKING:
    from llama_index.core.llms import LLM


def synthesize_with_system_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    llm: LLM,
    *,
    system_prompt: str,
) -> RagAnswer:
    """Synthesize an answer using an explicit sandbox system prompt."""
    if not chunks:
        return answer_without_context(question)
    language = detect_query_language(question)
    context = "\n\n".join(chunk.text for chunk in chunks)
    prompt = (
        f"{system_prompt.strip()}\n\nContext:\n{context}\n\nQuestion: {question.strip()}\n\nAnswer:"
    )
    response = llm.complete(prompt)
    answer_text = getattr(response, "text", str(response))
    return RagAnswer(answer=str(answer_text), language=language, sources=chunks)
