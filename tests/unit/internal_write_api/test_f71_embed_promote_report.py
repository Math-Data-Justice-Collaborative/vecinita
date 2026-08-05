"""T120.3b - pure builder unit tests for embed-promote report (no Postgres).

[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-235]
"""

from __future__ import annotations

from uuid import UUID

import pytest
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    LEGACY_E0_EMBEDDING_MODEL_ID,
)
from vecinita_internal_write_api.embed_promote_report import (
    aggregate_locale_metrics,
    merge_candidate_baseline,
    scaffold_embed_promote_report,
)
from vecinita_shared_schemas.json_types import as_json_object


@pytest.mark.unit
def test_scaffold_embed_promote_report_en_es_columns() -> None:
    """Scaffold always exposes EN/ES Hy1 + baseline_e0 keys (AC-ME3)."""
    run_id = UUID("33333333-3333-3333-3333-333333333333")
    report = scaffold_embed_promote_report(
        rebuild_run_id=run_id,
        candidate_embedding_model_id=DEFAULT_EMBEDDING_MODEL_ID,
    )
    payload = as_json_object(report.model_dump(mode="python"))
    assert payload.get("candidate_embedding_model_id") == DEFAULT_EMBEDDING_MODEL_ID
    assert payload.get("baseline_embedding_model_id") == LEGACY_E0_EMBEDDING_MODEL_ID
    assert payload.get("dense_available") is False
    by_lang = as_json_object(payload["by_language"])
    for lang in ("en", "es"):
        lang_metrics = as_json_object(by_lang[lang])
        assert "answer_relevancy" in lang_metrics
        assert "faithfulness" in lang_metrics
        baseline = as_json_object(lang_metrics["baseline_e0"])
        assert "answer_relevancy" in baseline
        assert "faithfulness" in baseline


@pytest.mark.unit
def test_aggregate_and_merge_sets_dense_when_hit_at_k_present() -> None:
    """TC-236: dense_available flips on when hit_at_k/mean_rank present."""
    candidate_items: list[dict[str, object]] = [
        {
            "locale": "en",
            "metrics": {
                "answer_relevancy": 0.7,
                "faithfulness": 0.8,
                "custom_scores": {"hit_at_k": 0.9, "mean_rank": 1.2},
            },
        },
        {
            "locale": "es",
            "metrics": {
                "answer_relevancy": 0.6,
                "faithfulness": 0.75,
                "custom_scores": {"hit_at_k": 0.85, "mean_rank": 1.5},
            },
        },
    ]
    baseline_items: list[dict[str, object]] = [
        {
            "locale": "en",
            "metrics": {
                "answer_relevancy": 0.65,
                "faithfulness": 0.7,
                "custom_scores": {"hit_at_k": 0.8, "mean_rank": 2.0},
            },
        },
        {
            "locale": "es",
            "metrics": {
                "answer_relevancy": 0.55,
                "faithfulness": 0.68,
                "custom_scores": {"hit_at_k": 0.7, "mean_rank": 2.4},
            },
        },
    ]
    candidate = aggregate_locale_metrics(candidate_items)
    baseline = aggregate_locale_metrics(baseline_items)
    by_language, dense = merge_candidate_baseline(candidate=candidate, baseline=baseline)
    assert dense is True
    assert by_language["en"].hit_at_k == pytest.approx(0.9)
    assert by_language["en"].mean_rank == pytest.approx(1.2)
    assert by_language["en"].baseline_e0.hit_at_k == pytest.approx(0.8)
    assert by_language["es"].answer_relevancy == pytest.approx(0.6)
    assert by_language["es"].baseline_e0.faithfulness == pytest.approx(0.68)
