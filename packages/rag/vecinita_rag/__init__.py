"""Vecinita RAG package — LlamaIndex + pgvector (F4, F5, F42)."""

from vecinita_rag.constants import (
    DEFAULT_TOP_K,
    EMBEDDING_DIMENSION,
    NO_CONTEXT_MESSAGE_EN,
    NO_CONTEXT_MESSAGE_ES,
)
from vecinita_rag.engine import (
    answer_from_chunks,
    answer_without_context,
    build_query_engine,
    build_retriever,
    synthesize_with_llm,
)
from vecinita_rag.language import detect_query_language, no_context_message
from vecinita_rag.multi_query import (
    heuristic_rewrites,
    merge_multi_query_hits,
    multi_query_retrieve,
)
from vecinita_rag.packing import pack_chunks, pack_p1
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RagAnswer, RetrievedChunk

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_TOP_K",
    "EMBEDDING_DIMENSION",
    "NO_CONTEXT_MESSAGE_EN",
    "NO_CONTEXT_MESSAGE_ES",
    "CorpusPgvectorRetriever",
    "RagAnswer",
    "RetrievedChunk",
    "answer_from_chunks",
    "answer_without_context",
    "build_query_engine",
    "build_retriever",
    "detect_query_language",
    "heuristic_rewrites",
    "merge_multi_query_hits",
    "multi_query_retrieve",
    "no_context_message",
    "pack_chunks",
    "pack_p1",
    "synthesize_with_llm",
]
