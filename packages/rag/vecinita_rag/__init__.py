"""Vecinita RAG package - LlamaIndex + pgvector (F4, F5, F42-F44)."""

from vecinita_rag.cache import (
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_CACHE_TTL_S,
    DEFAULT_SEMANTIC_THRESHOLD,
    AnswerCache,
    CachedAnswer,
    CacheHitKind,
    CascadeRequest,
    cascade_lookup,
    content_hash,
    normalize_query,
)
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
from vecinita_rag.rerank import (
    DEFAULT_CE_MODEL_ID,
    DEFAULT_CE_TOP_N,
    CallableCrossEncoderScorer,
    CrossEncoderScorer,
    merge_ce_rerank,
    rerank_with_scorer,
)
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.soft_language import SoftLanguageResult, soft_language_retrieve
from vecinita_rag.types import RagAnswer, RetrievedChunk

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CACHE_MAX_ENTRIES",
    "DEFAULT_CACHE_TTL_S",
    "DEFAULT_CE_MODEL_ID",
    "DEFAULT_CE_TOP_N",
    "DEFAULT_SEMANTIC_THRESHOLD",
    "DEFAULT_TOP_K",
    "EMBEDDING_DIMENSION",
    "NO_CONTEXT_MESSAGE_EN",
    "NO_CONTEXT_MESSAGE_ES",
    "AnswerCache",
    "CacheHitKind",
    "CachedAnswer",
    "CallableCrossEncoderScorer",
    "CascadeRequest",
    "CorpusPgvectorRetriever",
    "CrossEncoderScorer",
    "RagAnswer",
    "RetrievedChunk",
    "SoftLanguageResult",
    "answer_from_chunks",
    "answer_without_context",
    "build_query_engine",
    "build_retriever",
    "cascade_lookup",
    "content_hash",
    "detect_query_language",
    "heuristic_rewrites",
    "merge_ce_rerank",
    "merge_multi_query_hits",
    "multi_query_retrieve",
    "no_context_message",
    "normalize_query",
    "pack_chunks",
    "pack_p1",
    "rerank_with_scorer",
    "soft_language_retrieve",
    "synthesize_with_llm",
]
