"""Unit tests for F43 H1 answer / retrieval cache (TC-176-178, AC-BB1-BB3)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_rag.cache import (
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_CACHE_TTL_S,
    DEFAULT_SEMANTIC_THRESHOLD,
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
_CORPUS_V2 = "corpus-v2"
_NEAR_THRESHOLD = 0.95
_BELOW_THRESHOLD = 0.80


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


def test_semantic_cache_hits_above_threshold() -> None:
    """TC-177: cosine >= 0.92 yields semantic hit (AC-BB2)."""
    emb_a = (1.0, 0.0, 0.0)
    emb_b = (_NEAR_THRESHOLD, (1.0 - _NEAR_THRESHOLD**2) ** 0.5, 0.0)
    cache = AnswerCache(
        corpus_version=_CORPUS_V1,
        semantic_threshold=DEFAULT_SEMANTIC_THRESHOLD,
    )
    cache.store_answer(_QUERY, _LOCALE, _cached_answer(embedding=emb_a))

    hit, answer, _chunks = cascade_lookup(
        cache,
        CascadeRequest(
            query="Capital city of France?",
            locale=_LOCALE,
            query_embedding=emb_b,
        ),
    )

    assert hit == CacheHitKind.SEMANTIC
    assert answer is not None
    assert answer.answer == _ANSWER


def test_semantic_cache_misses_below_threshold() -> None:
    """TC-177: cosine below threshold continues (miss -> not semantic)."""
    emb_a = (1.0, 0.0, 0.0)
    emb_b = (_BELOW_THRESHOLD, (1.0 - _BELOW_THRESHOLD**2) ** 0.5, 0.0)
    cache = AnswerCache(
        corpus_version=_CORPUS_V1,
        semantic_threshold=DEFAULT_SEMANTIC_THRESHOLD,
    )
    cache.store_answer(_QUERY, _LOCALE, _cached_answer(embedding=emb_a))

    hit, answer, _chunks = cascade_lookup(
        cache,
        CascadeRequest(
            query="Unrelated question about weather",
            locale=_LOCALE,
            query_embedding=emb_b,
        ),
    )

    assert hit != CacheHitKind.SEMANTIC
    assert answer is None


def test_cache_ttl_expires_exact_entry() -> None:
    """TC-178: entries expire after TTL seconds (AC-BB3)."""
    cache = AnswerCache(
        corpus_version=_CORPUS_V1,
        ttl_s=DEFAULT_CACHE_TTL_S,
        now_fn=lambda: 1000.0,
    )
    cache.store_answer(_QUERY, _LOCALE, _cached_answer())

    cache.now_fn = lambda: 1000.0 + float(DEFAULT_CACHE_TTL_S) + 1.0

    hit, answer, _chunks = cascade_lookup(
        cache,
        CascadeRequest(query=_QUERY, locale=_LOCALE),
    )

    assert hit == CacheHitKind.NONE
    assert answer is None


def test_cache_max_entries_evicts_lru() -> None:
    """TC-178: max_entries enforces LRU eviction (AC-BB3)."""
    cache = AnswerCache(
        corpus_version=_CORPUS_V1,
        max_entries=2,
        ttl_s=DEFAULT_CACHE_TTL_S,
    )
    assert DEFAULT_CACHE_MAX_ENTRIES >= 16
    cache.store_answer("q1", _LOCALE, _cached_answer())
    cache.store_answer("q2", _LOCALE, _cached_answer())
    cache.store_answer("q3", _LOCALE, _cached_answer())

    hit1, _, _ = cascade_lookup(
        cache,
        CascadeRequest(query="q1", locale=_LOCALE),
    )
    hit3, answer3, _ = cascade_lookup(
        cache,
        CascadeRequest(query="q3", locale=_LOCALE),
    )

    assert hit1 == CacheHitKind.NONE
    assert hit3 == CacheHitKind.EXACT
    assert answer3 is not None


def test_cache_corpus_version_bust_clears_entries() -> None:
    """TC-178: corpus version change busts cache (AC-BB3 / ADR-040)."""
    cache = AnswerCache(corpus_version=_CORPUS_V1)
    cache.store_answer(_QUERY, _LOCALE, _cached_answer())
    cache.bust(corpus_version=_CORPUS_V2)

    hit, answer, _chunks = cascade_lookup(
        cache,
        CascadeRequest(query=_QUERY, locale=_LOCALE),
    )

    assert hit == CacheHitKind.NONE
    assert answer is None
    assert cache.corpus_version == _CORPUS_V2
