"""T120.3b red - F71 embed-promote report shape (TC-235/236 / AC-ME3-ME4).

[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-235]
[Spec: docs/acceptance-criteria.md §AC-ME3]
"""

from __future__ import annotations

import pytest
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    LEGACY_E0_EMBEDDING_MODEL_ID,
)
from vecinita_shared_schemas.internal_write import EmbedPromoteReportResponse
from vecinita_shared_schemas.json_types import as_json_object


@pytest.mark.unit
def test_embed_promote_report_schema_requires_en_es_hy1_vs_e0() -> None:
    """TC-235: report carries EN/ES rel+faith vs E0 baseline columns."""
    report = EmbedPromoteReportResponse.model_validate(
        {
            "rebuild_run_id": "11111111-1111-1111-1111-111111111111",
            "candidate_embedding_model_id": DEFAULT_EMBEDDING_MODEL_ID,
            "baseline_embedding_model_id": LEGACY_E0_EMBEDDING_MODEL_ID,
            "dense_available": False,
            "by_language": {
                "en": {
                    "answer_relevancy": 0.72,
                    "faithfulness": 0.81,
                    "baseline_e0": {
                        "answer_relevancy": 0.70,
                        "faithfulness": 0.80,
                    },
                },
                "es": {
                    "answer_relevancy": 0.65,
                    "faithfulness": 0.78,
                    "baseline_e0": {
                        "answer_relevancy": 0.60,
                        "faithfulness": 0.75,
                    },
                },
            },
        }
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
        assert lang_metrics.get("hit_at_k") is None
        assert lang_metrics.get("mean_rank") is None


@pytest.mark.unit
def test_embed_promote_report_includes_dense_when_available() -> None:
    """TC-236: hit_at_k + mean_rank present when dense_available is true."""
    report = EmbedPromoteReportResponse.model_validate(
        {
            "rebuild_run_id": "22222222-2222-2222-2222-222222222222",
            "candidate_embedding_model_id": DEFAULT_EMBEDDING_MODEL_ID,
            "baseline_embedding_model_id": LEGACY_E0_EMBEDDING_MODEL_ID,
            "dense_available": True,
            "by_language": {
                "en": {
                    "answer_relevancy": 0.7,
                    "faithfulness": 0.8,
                    "hit_at_k": 0.9,
                    "mean_rank": 1.5,
                    "baseline_e0": {
                        "answer_relevancy": 0.6,
                        "faithfulness": 0.7,
                        "hit_at_k": 0.8,
                        "mean_rank": 2.0,
                    },
                },
                "es": {
                    "answer_relevancy": 0.6,
                    "faithfulness": 0.7,
                    "hit_at_k": 0.85,
                    "mean_rank": 1.8,
                    "baseline_e0": {
                        "answer_relevancy": 0.55,
                        "faithfulness": 0.65,
                        "hit_at_k": 0.75,
                        "mean_rank": 2.2,
                    },
                },
            },
        }
    )
    by_lang = as_json_object(as_json_object(report.model_dump(mode="python"))["by_language"])
    for lang in ("en", "es"):
        lang_metrics = as_json_object(by_lang[lang])
        assert lang_metrics.get("hit_at_k") is not None
        assert lang_metrics.get("mean_rank") is not None
