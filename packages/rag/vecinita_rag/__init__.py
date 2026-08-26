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
from vecinita_rag.chat_retrieve import retrieve_chat_chunks
from vecinita_rag.constants import (
    DEFAULT_TOP_K,
    EMBEDDING_DIMENSION,
    NO_CONTEXT_MESSAGE_EN,
    NO_CONTEXT_MESSAGE_ES,
)
from vecinita_rag.display_title import coalesce_document_title
from vecinita_rag.engine import (
    answer_from_chunks,
    answer_without_context,
    build_query_engine,
    build_retriever,
    synthesize_with_llm,
)
from vecinita_rag.es_esl_supplement import (
    merge_es_esl_retrieval_for_r6,
    merge_retrieved_chunks_by_score,
    should_supplement_en_for_es_esl_query,
)
from vecinita_rag.language import detect_query_language, no_context_message
from vecinita_rag.multi_query import (
    heuristic_rewrites,
    merge_multi_query_hits,
    multi_query_retrieve,
)
from vecinita_rag.pipeline_knobs import (
    RagPipelineKnobs,
    normalize_rag_pipeline_knobs,
    rag_pipeline_knobs_from_env,
    retrieve_eval_packed,
    retrieve_multi_query_packed,
)
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
    "RagPipelineKnobs",
    "RetrievedChunk",
    "SoftLanguageResult",
    "answer_from_chunks",
    "answer_without_context",
    "build_query_engine",
    "build_retriever",
    "cascade_lookup",
    "coalesce_document_title",
    "content_hash",
    "detect_query_language",
    "heuristic_rewrites",
    "merge_ce_rerank",
    "merge_es_esl_retrieval_for_r6",
    "merge_multi_query_hits",
    "merge_retrieved_chunks_by_score",
    "multi_query_retrieve",
    "no_context_message",
    "normalize_query",
    "normalize_rag_pipeline_knobs",
    "pack_chunks",
    "pack_p1",
    "rag_pipeline_knobs_from_env",
    "rerank_with_scorer",
    "retrieve_chat_chunks",
    "retrieve_eval_packed",
    "retrieve_multi_query_packed",
    "should_supplement_en_for_es_esl_query",
    "soft_language_retrieve",
    "synthesize_with_llm",
]
