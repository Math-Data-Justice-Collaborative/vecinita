"""Query engine assembly (F4) — LlamaIndex retriever + optional LLM synthesis."""

from __future__ import annotations

from collections.abc import Callable

from llama_index.core.llms import LLM
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode, get_response_synthesizer
from llama_index.core.schema import NodeWithScore

from vecinita_rag.language import detect_query_language, no_context_message
from vecinita_rag.retriever import CorpusPgvectorRetriever, chunks_to_nodes
from vecinita_rag.types import RagAnswer, RetrievedChunk

EmbedFn = Callable[[str], list[float]]


def build_retriever(
    embed_fn: EmbedFn,
    *,
    database_url: str | None = None,
    top_k: int = 5,
    score_threshold: float | None = None,
) -> CorpusPgvectorRetriever:
    return CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=database_url,
        top_k=top_k,
        score_threshold=score_threshold,
    )


def build_query_engine(
    embed_fn: EmbedFn,
    llm: LLM,
    *,
    database_url: str | None = None,
    top_k: int = 5,
    score_threshold: float | None = None,
) -> RetrieverQueryEngine:
    retriever = build_retriever(
        embed_fn,
        database_url=database_url,
        top_k=top_k,
        score_threshold=score_threshold,
    )
    synthesizer = get_response_synthesizer(llm=llm, response_mode=ResponseMode.COMPACT)
    return RetrieverQueryEngine(retriever=retriever, response_synthesizer=synthesizer)


def answer_without_context(question: str) -> RagAnswer:
    language = detect_query_language(question)
    return RagAnswer(answer=no_context_message(language), language=language, sources=[])


def answer_from_chunks(
    question: str,
    chunks: list[RetrievedChunk],
    *,
    answer_text: str | None = None,
) -> RagAnswer:
    language = detect_query_language(question)
    if not chunks:
        return answer_without_context(question)
    if answer_text is None:
        # Synthesis deferred to caller/LLM; concatenate top chunk for smoke paths.
        answer_text = chunks[0].text
    return RagAnswer(answer=answer_text, language=language, sources=chunks)


def synthesize_with_llm(
    question: str,
    chunks: list[RetrievedChunk],
    llm: LLM,
) -> RagAnswer:
    if not chunks:
        return answer_without_context(question)
    language = detect_query_language(question)
    nodes: list[NodeWithScore] = chunks_to_nodes(chunks)
    synthesizer = get_response_synthesizer(llm=llm, response_mode=ResponseMode.COMPACT)
    response = synthesizer.synthesize(question, nodes)
    return RagAnswer(answer=str(response), language=language, sources=chunks)
