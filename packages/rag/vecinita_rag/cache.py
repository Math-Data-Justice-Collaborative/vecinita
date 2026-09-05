"""In-process H1 answer / retrieval cache cascade (F43, ADR-042).

Cascade order: exact → semantic → retrieve → (caller generate).
Keys are content-hashes of normalized query + locale (ADR-004).
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from collections import OrderedDict
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from vecinita_rag.types import RetrievedChunk

DEFAULT_CACHE_TTL_S = 3600
DEFAULT_CACHE_MAX_ENTRIES = 1024
DEFAULT_SEMANTIC_THRESHOLD = 0.92

_WS_RE = re.compile(r"\s+")


class CacheHitKind(StrEnum):
    """Observability enum for ask/stream ``cache_hit`` (api-contract)."""

    NONE = "none"
    EXACT = "exact"
    SEMANTIC = "semantic"
    RETRIEVE = "retrieve"


@dataclass(frozen=True)
class CachedAnswer:
    """Cached synthesis result (answer + sources + optional query embedding)."""

    answer: str
    language: str
    sources: tuple[RetrievedChunk, ...]
    query_embedding: tuple[float, ...] | None = None


@dataclass
class _CacheEntry:
    """Internal LRU entry for answer and/or retrieve tiers."""

    answer: CachedAnswer | None
    chunks: tuple[RetrievedChunk, ...] | None
    expires_at: float


def normalize_query(query: str, locale: str) -> str:
    """Normalize query + locale for content-hash keys (lowercase, collapse ws)."""
    cleaned = _WS_RE.sub(" ", query.strip().lower())
    loc = locale.strip().lower()
    return f"{loc}\0{cleaned}"


def content_hash(query: str, locale: str) -> str:
    """SHA-256 hex digest of normalized query+locale (ADR-004 content-hash)."""
    normalized = normalize_query(query, locale)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity; returns 0.0 if either vector has zero magnitude."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b, strict=True):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


class AnswerCache:
    """Process-local LRU answer/retrieve cache with TTL and corpus bust."""

    def __init__(
        self,
        *,
        ttl_s: int = DEFAULT_CACHE_TTL_S,
        max_entries: int = DEFAULT_CACHE_MAX_ENTRIES,
        semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
        corpus_version: str = "",
        now_fn: Callable[[], float] | None = None,
    ) -> None:
        """Configure TTL, LRU size, semantic threshold, and optional clock."""
        if ttl_s < 1:
            msg = "ttl_s must be >= 1"
            raise ValueError(msg)
        if max_entries < 1:
            msg = "max_entries must be >= 1"
            raise ValueError(msg)
        if not 0.0 <= semantic_threshold <= 1.0:
            msg = "semantic_threshold must be in [0, 1]"
            raise ValueError(msg)
        self.ttl_s = ttl_s
        self.max_entries = max_entries
        self.semantic_threshold = semantic_threshold
        self.corpus_version = corpus_version
        self.now_fn: Callable[[], float] = now_fn if now_fn is not None else time.time
        self._entries: OrderedDict[str, _CacheEntry] = OrderedDict()

    def bust(self, *, corpus_version: str) -> None:
        """Clear all entries and adopt a new corpus/version stamp."""
        self._entries.clear()
        self.corpus_version = corpus_version

    def store_answer(self, query: str, locale: str, answer: CachedAnswer) -> None:
        """Store or refresh an answer (and embedding) under the content-hash key."""
        key = content_hash(query, locale)
        now = self.now_fn()
        existing = self._entries.get(key)
        chunks = existing.chunks if existing is not None else None
        self._entries[key] = _CacheEntry(
            answer=answer,
            chunks=chunks,
            expires_at=now + float(self.ttl_s),
        )
        self._entries.move_to_end(key)
        self._evict_if_needed()

    def store_retrieve(
        self,
        query: str,
        locale: str,
        chunks: Sequence[RetrievedChunk],
    ) -> None:
        """Store retrieve-result chunks under the content-hash key."""
        key = content_hash(query, locale)
        now = self.now_fn()
        existing = self._entries.get(key)
        answer = existing.answer if existing is not None else None
        self._entries[key] = _CacheEntry(
            answer=answer,
            chunks=tuple(chunks),
            expires_at=now + float(self.ttl_s),
        )
        self._entries.move_to_end(key)
        self._evict_if_needed()

    def lookup_exact(self, query: str, locale: str) -> CachedAnswer | None:
        """Return a non-expired exact answer or None."""
        entry = self._get_live(content_hash(query, locale))
        if entry is None or entry.answer is None:
            return None
        return entry.answer

    def lookup_retrieve(
        self,
        query: str,
        locale: str,
    ) -> tuple[RetrievedChunk, ...] | None:
        """Return non-expired cached retrieve chunks or None."""
        entry = self._get_live(content_hash(query, locale))
        if entry is None or entry.chunks is None:
            return None
        return entry.chunks

    def lookup_semantic(
        self,
        query_embedding: Sequence[float],
        *,
        locale: str,
    ) -> CachedAnswer | None:
        """Best cosine match ≥ threshold among same-locale answers with embeddings."""
        loc = locale.strip().lower()
        best: CachedAnswer | None = None
        best_score = -1.0
        # Snapshot keys to allow OrderedDict mutation during live checks.
        for key in list(self._entries):
            entry = self._get_live(key)
            if entry is None or entry.answer is None:
                continue
            emb = entry.answer.query_embedding
            if emb is None:
                continue
            if entry.answer.language.strip().lower() != loc:
                continue
            score = cosine_similarity(query_embedding, emb)
            if score >= self.semantic_threshold and score > best_score:
                best_score = score
                best = entry.answer
        return best

    def _get_live(self, key: str) -> _CacheEntry | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if self.now_fn() >= entry.expires_at:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return entry

    def _evict_if_needed(self) -> None:
        while len(self._entries) > self.max_entries:
            _ = self._entries.popitem(last=False)


@dataclass(frozen=True)
class CascadeRequest:
    """Inputs for one H1 cascade lookup (keeps ``cascade_lookup`` arity low)."""

    query: str
    locale: str
    query_embedding: Sequence[float] | None = None
    generate: Callable[[], CachedAnswer] | None = None
    retrieve: Callable[[], Sequence[RetrievedChunk]] | None = None


def cascade_lookup(
    cache: AnswerCache,
    request: CascadeRequest,
) -> tuple[CacheHitKind, CachedAnswer | None, tuple[RetrievedChunk, ...] | None]:
    """Run H1 cascade: exact -> semantic -> retrieve -> optional generate/store.

    ``generate`` / ``retrieve`` are only invoked on miss of earlier tiers.
    Exact/semantic hits skip both. Retrieve hits skip ``retrieve`` but not
    ``generate`` (caller synthesizes from cached chunks when desired).
    """
    query = request.query
    locale = request.locale
    exact = cache.lookup_exact(query, locale)
    if exact is not None:
        return CacheHitKind.EXACT, exact, None

    if request.query_embedding is not None:
        semantic = cache.lookup_semantic(request.query_embedding, locale=locale)
        if semantic is not None:
            return CacheHitKind.SEMANTIC, semantic, None

    cached_chunks = cache.lookup_retrieve(query, locale)
    if cached_chunks is not None:
        return CacheHitKind.RETRIEVE, None, cached_chunks

    if request.retrieve is not None:
        chunks = tuple(request.retrieve())
        cache.store_retrieve(query, locale, chunks)
        if request.generate is None:
            return CacheHitKind.NONE, None, chunks

    if request.generate is not None:
        answer = request.generate()
        cache.store_answer(query, locale, answer)
        return CacheHitKind.NONE, answer, None

    return CacheHitKind.NONE, None, None
