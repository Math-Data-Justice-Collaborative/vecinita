"""T95.5: F36 harness warm/cold cache cost + hit-rate cells (F43 / AC-BB2)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest
from vecinita_eval.cache_harness import (
    CacheRowObservation,
    run_exact_warm_cold,
    summarize_cache_rows,
)
from vecinita_eval.experiments import aggregate_experiments
from vecinita_rag.cache import CachedAnswer
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from vecinita_shared_schemas.json_types import JsonObject

pytestmark = pytest.mark.unit

_ANSWER = "Food pantry hours are posted Mondays."
_COLD_GENERATE_CALLS = 2


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text=_ANSWER,
        score=0.9,
        title="Pantry",
        url="https://example.org/pantry",
        language="en",
    )


def test_summarize_cache_rows_hit_rate_and_relative_cost() -> None:
    """Hit-rate and relative LLM cost cells from per-row cache observations."""
    cold = summarize_cache_rows(
        [
            CacheRowObservation(cache_hit="none", llm_calls=1, answer=_ANSWER),
            CacheRowObservation(cache_hit="none", llm_calls=1, answer=_ANSWER),
        ]
    )
    warm = summarize_cache_rows(
        [
            CacheRowObservation(cache_hit="exact", llm_calls=0, answer=_ANSWER),
            CacheRowObservation(cache_hit="exact", llm_calls=0, answer=_ANSWER),
        ]
    )
    assert cold.hit_rate == 0.0
    assert cold.mean_llm_calls == 1.0
    assert cold.relative_llm_cost == 1.0
    assert warm.exact_hit_rate == 1.0
    assert warm.hit_rate == 1.0
    assert warm.mean_llm_calls == 0.0
    assert warm.relative_llm_cost == 0.0


def test_run_exact_warm_cold_skips_llm_on_warm_and_keeps_answers() -> None:
    """Cold miss → warm exact; warm quality matches cold answers (AC-BB2 / H0)."""
    generate_calls = 0

    def _generate(query: str, locale: str) -> CachedAnswer:
        nonlocal generate_calls
        _ = (query, locale)
        generate_calls += 1
        return CachedAnswer(
            answer=_ANSWER,
            language="en",
            sources=(_chunk(),),
        )

    cold, warm, cold_answers, warm_answers = run_exact_warm_cold(
        questions=(("What are the food pantry hours?", "en"), ("Pantry hours?", "en")),
        generate=_generate,
    )
    assert generate_calls == _COLD_GENERATE_CALLS
    assert cold.hit_rate == 0.0
    assert cold.mean_llm_calls == 1.0
    assert warm.exact_hit_rate == 1.0
    assert warm.relative_llm_cost == 0.0
    assert warm_answers == cold_answers


def test_experiment_aggregation_includes_cache_cost_cells() -> None:
    """aggregate_experiments averages cache_hit_rate and relative_llm_cost when present."""
    experiments: list[JsonObject] = [
        {
            "experiment_id": "cache-demo",
            "cells": [
                {
                    "config": {
                        "model_id": "qwen2.5:1.5b-instruct",
                        "temperature": 0.2,
                        "top_k": 5,
                        "prompt_name": "default",
                        "pass": "warm",
                    },
                    "averages": {
                        "retrieval_relevance": 1.0,
                        "faithfulness": 0.95,
                        "answer_relevancy": 0.9,
                        "wall_time_s": 1.0,
                        "latency_p95_ms": 50.0,
                        "cache_hit_rate": 1.0,
                        "relative_llm_cost": 0.0,
                    },
                }
            ],
        }
    ]
    aggregated = aggregate_experiments(
        experiments,
        group_by=("model_id", "pass"),
        metrics=("cache_hit_rate", "relative_llm_cost", "answer_relevancy"),
    )
    groups = aggregated["groups"]
    assert isinstance(groups, list)
    assert len(cast("list[object]", groups)) == 1
    means = as_json_object(as_json_object(cast("object", groups[0]))["means"])
    assert means["cache_hit_rate"] == 1.0
    assert means["relative_llm_cost"] == 0.0
