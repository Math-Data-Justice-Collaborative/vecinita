"""T120.3b/T120.5 - embed-promote report builder + route branch coverage.

[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-235]
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Self, cast
from uuid import UUID, uuid4

import pytest
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    LEGACY_E0_EMBEDDING_MODEL_ID,
)
from vecinita_internal_write_api.embed_promote_report import (
    EmbedPromoteReportNotFoundError,
    aggregate_locale_metrics,
    build_embed_promote_report,
    merge_candidate_baseline,
    scaffold_embed_promote_report,
)
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_object_get, json_str
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi.testclient import TestClient


class _FakeMappings:
    def __init__(
        self,
        *,
        first_row: dict[str, object] | None = None,
        rows: Sequence[dict[str, object]] | None = None,
    ) -> None:
        self._first = first_row
        self._rows = list(rows or [])

    def first(self) -> dict[str, object] | None:
        return self._first

    def all(self) -> list[dict[str, object]]:
        return list(self._rows)


class _FakeResult:
    def __init__(self, mappings: _FakeMappings) -> None:
        self._mappings = mappings

    def mappings(self) -> _FakeMappings:
        return self._mappings


class _FakeConn:
    def __init__(self, results: list[_FakeResult]) -> None:
        self._results = results
        self._idx = 0

    def execute(self, *_args: object, **_kwargs: object) -> _FakeResult:
        result = self._results[self._idx]
        self._idx += 1
        return result

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


class _FakeEngine:
    def __init__(self, results: list[_FakeResult]) -> None:
        self._results = results

    def connect(self) -> _FakeConn:
        return _FakeConn(self._results)


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


@pytest.mark.unit
def test_aggregate_skips_unknown_locale_and_bool_scores() -> None:
    """Unknown locales and bool metric values are ignored."""
    items: list[dict[str, object]] = [
        {"locale": "fr", "metrics": {"answer_relevancy": 0.9, "faithfulness": 0.9}},
        {"locale": "en", "metrics": {"answer_relevancy": True, "faithfulness": 0.5}},
        {"locale": "EN", "metrics": "not-a-dict"},
        {
            "locale": "es",
            "metrics": {"answer_relevancy": 0.4, "hit_at_k": 0.77, "custom_scores": "x"},
        },
    ]
    aggregated = aggregate_locale_metrics(items)
    assert aggregated["en"].answer_relevancy is None
    assert aggregated["en"].faithfulness == pytest.approx(0.5)
    assert aggregated["es"].answer_relevancy == pytest.approx(0.4)
    assert aggregated["es"].hit_at_k == pytest.approx(0.77)
    assert aggregated["es"].faithfulness is None


@pytest.mark.unit
def test_merge_without_dense_strips_rank_fields() -> None:
    """When no dense scores exist, hit_at_k/mean_rank stay None."""
    candidate = aggregate_locale_metrics(
        [
            {
                "locale": "en",
                "metrics": {"answer_relevancy": 0.5, "faithfulness": 0.6},
            }
        ]
    )
    baseline = aggregate_locale_metrics(
        [
            {
                "locale": "en",
                "metrics": {"answer_relevancy": 0.4, "faithfulness": 0.55},
            }
        ]
    )
    by_language, dense = merge_candidate_baseline(candidate=candidate, baseline=baseline)
    assert dense is False
    assert by_language["en"].hit_at_k is None
    assert by_language["en"].mean_rank is None
    assert by_language["en"].baseline_e0.hit_at_k is None
    assert by_language["es"].answer_relevancy is None


@pytest.mark.unit
def test_build_embed_promote_report_not_found() -> None:
    """Missing rebuild_runs row raises EmbedPromoteReportNotFoundError."""
    engine = _FakeEngine(
        [
            _FakeResult(_FakeMappings(first_row=None)),
        ]
    )
    with pytest.raises(EmbedPromoteReportNotFoundError, match="rebuild run not found"):
        build_embed_promote_report(engine, rebuild_run_id=uuid4())  # type: ignore[arg-type]


@pytest.mark.unit
def test_build_embed_promote_report_scaffold_when_no_eval_items() -> None:
    """No linked eval items → EN/ES scaffold with candidate stamp."""
    run_id = uuid4()
    engine = _FakeEngine(
        [
            _FakeResult(
                _FakeMappings(
                    first_row={
                        "id": run_id,
                        "embedding_model_id": DEFAULT_EMBEDDING_MODEL_ID,
                    }
                )
            ),
            _FakeResult(_FakeMappings(rows=[])),
            _FakeResult(_FakeMappings(rows=[])),
        ]
    )
    report = build_embed_promote_report(engine, rebuild_run_id=run_id)  # type: ignore[arg-type]
    assert report.candidate_embedding_model_id == DEFAULT_EMBEDDING_MODEL_ID
    assert report.baseline_embedding_model_id == LEGACY_E0_EMBEDDING_MODEL_ID
    assert report.dense_available is False
    assert report.by_language["en"].answer_relevancy is None
    assert report.by_language["es"].baseline_e0.faithfulness is None


@pytest.mark.unit
def test_build_embed_promote_report_defaults_candidate_when_stamp_null() -> None:
    """Null embedding_model_id on rebuild_runs falls back to DEFAULT pin."""
    run_id = uuid4()
    engine = _FakeEngine(
        [
            _FakeResult(_FakeMappings(first_row={"id": run_id, "embedding_model_id": None})),
            _FakeResult(_FakeMappings(rows=[])),
            _FakeResult(_FakeMappings(rows=[])),
        ]
    )
    report = build_embed_promote_report(engine, rebuild_run_id=run_id)  # type: ignore[arg-type]
    assert report.candidate_embedding_model_id == DEFAULT_EMBEDDING_MODEL_ID


@pytest.mark.unit
def test_build_embed_promote_report_merges_eval_items() -> None:
    """Linked candidate + live baseline eval items populate Hy1 columns."""
    run_id = uuid4()
    engine = _FakeEngine(
        [
            _FakeResult(
                _FakeMappings(
                    first_row={
                        "id": run_id,
                        "embedding_model_id": DEFAULT_EMBEDDING_MODEL_ID,
                    }
                )
            ),
            _FakeResult(
                _FakeMappings(
                    rows=[
                        {
                            "locale": "en",
                            "metrics": {
                                "answer_relevancy": 0.71,
                                "faithfulness": 0.82,
                            },
                        },
                        {
                            "locale": "es",
                            "metrics": {
                                "answer_relevancy": 0.61,
                                "faithfulness": 0.72,
                            },
                        },
                    ]
                )
            ),
            _FakeResult(
                _FakeMappings(
                    rows=[
                        {
                            "locale": "en",
                            "metrics": {
                                "answer_relevancy": 0.66,
                                "faithfulness": 0.77,
                            },
                        },
                        {
                            "locale": "es",
                            "metrics": {
                                "answer_relevancy": 0.56,
                                "faithfulness": 0.67,
                            },
                        },
                    ]
                )
            ),
        ]
    )
    report = build_embed_promote_report(engine, rebuild_run_id=run_id)  # type: ignore[arg-type]
    assert report.dense_available is False
    assert report.by_language["en"].answer_relevancy == pytest.approx(0.71)
    assert report.by_language["en"].baseline_e0.faithfulness == pytest.approx(0.77)
    assert report.by_language["es"].answer_relevancy == pytest.approx(0.61)
    assert report.by_language["es"].baseline_e0.answer_relevancy == pytest.approx(0.56)


@pytest.mark.unit
def test_get_embed_promote_report_route_ok_and_404(write_client: TestClient) -> None:
    """HTTP route returns scaffold for known run and 404 for unknown id."""
    create = write_client.post(
        "/internal/v1/rebuild/runs",
        json={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "completed",
            "embedding_model_id": DEFAULT_EMBEDDING_MODEL_ID,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 256,
            "chunk_tokenizer_id": DEFAULT_EMBEDDING_MODEL_ID,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.OK, create.text
    rebuild_run_id = json_str(as_json_object(cast("object", create.json())), "rebuild_run_id")

    report = write_client.get(
        f"/internal/v1/rebuild/{rebuild_run_id}/embed-promote-report",
        headers=auth_headers(),
    )
    assert report.status_code == HTTPStatus.OK, report.text
    payload = as_json_object(cast("object", report.json()))
    assert json_str(payload, "candidate_embedding_model_id") == DEFAULT_EMBEDDING_MODEL_ID
    assert json_str(payload, "baseline_embedding_model_id") == LEGACY_E0_EMBEDDING_MODEL_ID
    by_lang = json_object_get(payload, "by_language")
    for lang in ("en", "es"):
        lang_metrics = json_object_get(by_lang, lang)
        assert "answer_relevancy" in lang_metrics
        assert "faithfulness" in lang_metrics
        assert "baseline_e0" in lang_metrics

    missing = write_client.get(
        f"/internal/v1/rebuild/{uuid4()}/embed-promote-report",
        headers=auth_headers(),
    )
    assert missing.status_code == HTTPStatus.NOT_FOUND
