"""BUG-2026-09-09: empty / no-source answers must not poison exact cache."""

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

_QUERY = "Where can I get food assistance in Providence?"
_LOCALE = "en"
_EMPTY_MSG = "I don't have enough community corpus context to answer that question."


def _empty_answer() -> CachedAnswer:
    return CachedAnswer(
        answer=_EMPTY_MSG,
        language=_LOCALE,
        sources=(),
        query_embedding=(0.1, 0.2),
    )


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="Providence food pantry hours",
        score=0.91,
        title="Food pantry",
        url="https://example.org/pantry",
        language=_LOCALE,
    )


def _good_answer() -> CachedAnswer:
    return CachedAnswer(
        answer="Visit the community food pantry.",
        language=_LOCALE,
        sources=(_chunk(),),
        query_embedding=(0.1, 0.2),
    )


def test_store_answer_skips_empty_sources_no_exact_hit() -> None:
    """Empty-source refusals are not stored; lookup_exact stays a miss."""
    cache = AnswerCache(corpus_version="v1")
    cache.store_answer(_QUERY, _LOCALE, _empty_answer())
    assert cache.lookup_exact(_QUERY, _LOCALE) is None


def test_store_retrieve_skips_empty_chunks_no_retrieve_hit() -> None:
    """Empty retrieve results are not stored (avoids sticky empty RETRIEVE)."""
    cache = AnswerCache(corpus_version="v1")
    cache.store_retrieve(_QUERY, _LOCALE, ())
    assert cache.lookup_retrieve(_QUERY, _LOCALE) is None


_TWO_ATTEMPTS = 2


def test_cascade_empty_generate_does_not_exact_cache_poison_retry() -> None:
    """BUG-2026-09-09: first empty generate must not exact-hit on the next ask."""
    cache = AnswerCache(corpus_version="v1")
    generate_calls = 0
    retrieve_calls = 0

    def _retrieve() -> tuple[RetrievedChunk, ...]:
        nonlocal retrieve_calls
        retrieve_calls += 1
        if retrieve_calls == 1:
            return ()
        return (_chunk(),)

    def _generate() -> CachedAnswer:
        nonlocal generate_calls
        generate_calls += 1
        if generate_calls == 1:
            return _empty_answer()
        return _good_answer()

    hit1, ans1, _chunks1 = cascade_lookup(
        cache,
        CascadeRequest(
            query=_QUERY,
            locale=_LOCALE,
            retrieve=_retrieve,
            generate=_generate,
        ),
    )
    assert hit1 == CacheHitKind.NONE
    assert ans1 is not None
    assert ans1.sources == ()
    assert generate_calls == 1

    hit2, ans2, _chunks2 = cascade_lookup(
        cache,
        CascadeRequest(
            query=_QUERY,
            locale=_LOCALE,
            retrieve=_retrieve,
            generate=_generate,
        ),
    )
    assert hit2 == CacheHitKind.NONE
    assert ans2 is not None
    assert len(ans2.sources) == 1
    assert generate_calls == _TWO_ATTEMPTS
    assert retrieve_calls == _TWO_ATTEMPTS
