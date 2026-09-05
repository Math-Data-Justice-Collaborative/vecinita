"""ChatRAG retrieval pipeline: soft-language, ESL supplement, multi-query, CE rerank."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from vecinita_rag.es_esl_supplement import (
    merge_es_esl_retrieval_for_r6,
    should_supplement_en_for_es_esl_query,
)
from vecinita_rag.multi_query import merge_multi_query_hits, multi_query_retrieve
from vecinita_rag.rerank import rerank_with_scorer
from vecinita_rag.soft_language import soft_language_retrieve
from vecinita_rag.types import RetrievedChunk

if TYPE_CHECKING:
    from vecinita_rag.pipeline_knobs import RagPipelineKnobs
    from vecinita_rag.rerank import CrossEncoderScorer

RetrieveLangFn = Callable[
    [str, str | None, list[str] | None, int, float],
    list[RetrievedChunk],
]


def retrieve_lang_with_tag_fallback(  # noqa: PLR0913 — retrieve wiring needs lang/tags/k/threshold
    question: str,
    lang: str | None,
    *,
    retrieve_lang_fn: RetrieveLangFn,
    tag_slugs: list[str] | None,
    top_k: int,
    min_retrieval_score: float,
) -> list[RetrievedChunk]:
    """Retrieve with tag filter; retry without tags when the tagged pass is empty."""
    chunks = retrieve_lang_fn(question, lang, tag_slugs, top_k, min_retrieval_score)
    if not chunks and tag_slugs:
        chunks = retrieve_lang_fn(question, lang, None, top_k, min_retrieval_score)
    return chunks


def retrieve_once_with_language_layers(  # noqa: PLR0913 — language-layer retrieve wiring
    question: str,
    *,
    language: str,
    tag_slugs: list[str] | None,
    top_k: int,
    min_retrieval_score: float,
    retrieve_lang_fn: RetrieveLangFn,
    soft_language_fallback: bool,
) -> list[RetrievedChunk]:
    """Single-question retrieve with soft-language fallback and ES ESL EN supplement."""

    def _retrieve_lang(question_text: str, lang: str | None) -> list[RetrievedChunk]:
        return retrieve_lang_with_tag_fallback(
            question_text,
            lang,
            retrieve_lang_fn=retrieve_lang_fn,
            tag_slugs=tag_slugs,
            top_k=top_k,
            min_retrieval_score=min_retrieval_score,
        )

    chunks = soft_language_retrieve(
        question,
        language=language,
        retrieve_fn=_retrieve_lang,
        enabled=soft_language_fallback,
    ).chunks
    if should_supplement_en_for_es_esl_query(
        language=language,
        question=question,
        tag_slugs=tag_slugs,
    ):
        en_chunks = _retrieve_lang(question, "en")
        chunks = merge_es_esl_retrieval_for_r6(
            chunks,
            en_chunks,
            top_k=top_k,
        )
    return chunks


def retrieve_chat_chunks(  # noqa: PLR0913 — ChatRAG fan-out mirrors service retrieve contract
    questions: Sequence[str],
    *,
    language: str,
    tag_slugs: list[str] | None,
    top_k: int,
    min_retrieval_score: float,
    retrieve_lang_fn: RetrieveLangFn,
    knobs: RagPipelineKnobs,
    soft_language_fallback: bool = False,
    ce_enabled: bool = False,
    ce_scorer: CrossEncoderScorer | None = None,
    ce_top_n: int = 0,
    rerank_question: str,
) -> list[RetrievedChunk]:
    """Run ChatRAG retrieval fan-out (F42 multi-query + F81 refine + F45 CE rerank)."""
    retrieve_k = top_k
    if ce_enabled:
        retrieve_k = max(top_k, ce_top_n)

    def _retrieve_once(question: str) -> list[RetrievedChunk]:
        return retrieve_once_with_language_layers(
            question,
            language=language,
            tag_slugs=tag_slugs,
            top_k=retrieve_k,
            min_retrieval_score=min_retrieval_score,
            retrieve_lang_fn=retrieve_lang_fn,
            soft_language_fallback=soft_language_fallback,
        )

    groups: list[list[RetrievedChunk]] = []
    for question_text in questions:
        sub_chunks = multi_query_retrieve(
            question_text,
            locale=language,
            top_k=retrieve_k,
            retrieve_fn=_retrieve_once,
            enabled=knobs.multi_query,
            count=knobs.multi_query_count,
        )
        groups.append(sub_chunks)
    chunks = merge_multi_query_hits(groups, top_k=retrieve_k)
    if ce_enabled and ce_scorer is not None:
        return rerank_with_scorer(
            rerank_question,
            chunks,
            top_k=top_k,
            scorer=ce_scorer,
            score_threshold=min_retrieval_score,
        )
    return chunks
