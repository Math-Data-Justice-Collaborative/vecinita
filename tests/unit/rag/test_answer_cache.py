"""Unit tests for F43 H1 answer / retrieval cache (TC-176-178, AC-BB1-BB3)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_rag.cache import (
    AnswerCache,
    CachedAnswer,
    CacheHitKind,
    CascadeRequest,
    cascade_lookup,
)
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit

_QUERY = "What is the capital of France?"
_LOCALE = "en"
_ANSWER = "Paris is the capital of France."
_CORPUS_V1 = "corpus-v1"


def _chunk(*, text: str = "body", score: float = 0.9) -> RetrievedChunk:
    """Build a RetrievedChunk for cache payload tests."""
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text=text,
        score=score,
        title="Title",
        url="https://example.org/doc",
        language=_LOCALE,
    )


def _cached_answer(*, embedding: tuple[float, ...] | None = None) -> CachedAnswer:
    """Build a CachedAnswer with one source chunk."""
    return CachedAnswer(
        answer=_ANSWER,
        language=_LOCALE,
        sources=(_chunk(),),
        query_embedding=embedding,
    )


def test_exact_answer_cache_hit_skips_generate() -> None:
    """TC-176: exact answer hit returns cached answer and skips generate (AC-BB1)."""
    cache = AnswerCache(corpus_version=_CORPUS_V1)
    cache.store_answer(_QUERY, _LOCALE, _cached_answer())

    generate_calls = 0

    def _generate() -> CachedAnswer:
        nonlocal generate_calls
        generate_calls += 1
        return _cached_answer()

    hit, answer, chunks = cascade_lookup(
        cache,
        CascadeRequest(query=_QUERY, locale=_LOCALE, generate=_generate),
    )

    assert hit == CacheHitKind.EXACT
    assert answer is not None
    assert answer.answer == _ANSWER
    assert chunks is None
    assert generate_calls == 0


def test_exact_answer_cache_normalizes_whitespace_and_case() -> None:
    """TC-176: normalized query+locale shares the exact key."""
    cache = AnswerCache(corpus_version=_CORPUS_V1)
    cache.store_answer(_QUERY, _LOCALE, _cached_answer())

    hit, answer, _chunks = cascade_lookup(
        cache,
        CascadeRequest(query="  what is the capital of france?  ", locale=_LOCALE),
    )

    assert hit == CacheHitKind.EXACT
    assert answer is not None
    assert answer.answer == _ANSWER
