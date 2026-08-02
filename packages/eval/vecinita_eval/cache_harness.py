"""F43 / F36 harness: warm/cold cache cost + hit-rate cells (T95.5, AC-BB2).

Uses ``packages/rag`` H1 cascade so eval sweeps can report ``cache_hit_rate`` and
``relative_llm_cost`` beside quality metrics (H0 warm parity).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from vecinita_rag.cache import (
    AnswerCache,
    CachedAnswer,
    CacheHitKind,
    CascadeRequest,
    cascade_lookup,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

CacheHitLabel = str


@dataclass(frozen=True, slots=True)
class CacheRowObservation:
    """One ask observation for cache harness aggregation."""

    cache_hit: CacheHitLabel
    llm_calls: int
    answer: str


@dataclass(frozen=True, slots=True)
class CacheCellSummary:
    """Aggregate cells for a cold or warm cache pass."""

    hit_rate: float
    exact_hit_rate: float
    mean_llm_calls: float
    relative_llm_cost: float
    n: int


def summarize_cache_rows(rows: Sequence[CacheRowObservation]) -> CacheCellSummary:
    """Compute hit-rate and relative LLM cost from per-row observations.

    ``relative_llm_cost`` is mean LLM calls per row (1.0 = full generate every row;
    0.0 = all exact/semantic hits with no generate).
    """
    if not rows:
        return CacheCellSummary(
            hit_rate=0.0,
            exact_hit_rate=0.0,
            mean_llm_calls=0.0,
            relative_llm_cost=0.0,
            n=0,
        )
    n = len(rows)
    hits = sum(1 for row in rows if row.cache_hit != str(CacheHitKind.NONE))
    exact = sum(1 for row in rows if row.cache_hit == str(CacheHitKind.EXACT))
    mean_calls = sum(row.llm_calls for row in rows) / float(n)
    return CacheCellSummary(
        hit_rate=hits / float(n),
        exact_hit_rate=exact / float(n),
        mean_llm_calls=mean_calls,
        relative_llm_cost=mean_calls,
        n=n,
    )


def _cascade_once(
    store: AnswerCache,
    *,
    query: str,
    locale: str,
    generate: Callable[[str, str], CachedAnswer],
) -> CacheRowObservation:
    calls = 0

    def _generate() -> CachedAnswer:
        nonlocal calls
        calls += 1
        return generate(query, locale)

    hit, cached, _chunks = cascade_lookup(
        store,
        CascadeRequest(query=query, locale=locale, generate=_generate),
    )
    if cached is None:
        msg = "cascade_lookup with generate must return an answer"
        raise RuntimeError(msg)
    return CacheRowObservation(
        cache_hit=str(hit),
        llm_calls=calls,
        answer=cached.answer,
    )


def run_exact_warm_cold(
    *,
    questions: Sequence[tuple[str, str]],
    generate: Callable[[str, str], CachedAnswer],
    cache: AnswerCache | None = None,
) -> tuple[CacheCellSummary, CacheCellSummary, list[str], list[str]]:
    """Run cold then warm passes over the same questions via H1 exact cascade.

    Returns:
    -------
    tuple
        ``(cold_summary, warm_summary, cold_answers, warm_answers)``.
        Warm answers matching cold answers is the H0 quality gate for exact hits.
    """
    store = cache if cache is not None else AnswerCache()
    cold_obs: list[CacheRowObservation] = []
    warm_obs: list[CacheRowObservation] = []
    cold_answers: list[str] = []
    warm_answers: list[str] = []

    for query, locale in questions:
        observation = _cascade_once(store, query=query, locale=locale, generate=generate)
        cold_obs.append(observation)
        cold_answers.append(observation.answer)

    for query, locale in questions:
        observation = _cascade_once(store, query=query, locale=locale, generate=generate)
        warm_obs.append(observation)
        warm_answers.append(observation.answer)

    return (
        summarize_cache_rows(cold_obs),
        summarize_cache_rows(warm_obs),
        cold_answers,
        warm_answers,
    )
