"""Unit tests for eval run persistence and execution (F36, ADR-033)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from vecinita_eval.golden import GoldenRow
from vecinita_eval.runner import EvalSummary, RowMetrics, RowResult
from vecinita_internal_write_api.eval_service import (
    create_eval_run,
    execute_eval_run,
    get_eval_run,
    list_eval_runs,
)
from vecinita_shared_schemas.internal_write import EvalMetricsSummary

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

_EXPECTED_ROW_LATENCY_MS = 1500
_EXPECTED_METRIC_LATENCY_MS = 99


def _sample_row_result() -> RowResult:
    row = GoldenRow(
        id="community-food-pantry",
        locale="en",
        domain="community",
        question="When are food pantry hours updated?",
        retrieval_expectation="hit",
        required_facts=("hours",),
        expected_doc_url="fixture://corpus/en/community-resources.md",
    )
    return RowResult(
        row=row,
        retrieved_urls=[row.expected_doc_url or ""],
        answer="Food pantry hours are posted weekly.",
        metrics=RowMetrics(
            retrieval_pass=True,
            faithfulness=0.85,
            answer_relevancy=0.8,
            latency_ms=3100,
        ),
    )


def _sample_summary() -> EvalSummary:
    return EvalSummary(
        retrieval_relevance=0.91,
        faithfulness=0.72,
        answer_relevancy=0.68,
        latency_p95_ms=4200,
    )


@pytest.fixture
def eval_run_id(engine: Engine) -> UUID:
    """Create a pending eval run and delete it after the test."""
    created = create_eval_run(engine, corpus_profile="fixture")
    yield created.run_id
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM eval_run_items WHERE run_id = :id"),
            {"id": created.run_id},
        )
        conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": created.run_id})


def test_create_eval_run_inserts_pending_row(engine: Engine) -> None:
    """create_eval_run returns pending status and persists the row."""
    created = create_eval_run(engine, corpus_profile="fixture")
    try:
        assert created.status == "pending"
        listed = list_eval_runs(engine, page=1, page_size=20)
        assert any(item.run_id == created.run_id for item in listed.items)
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": created.run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": created.run_id})


def test_execute_eval_run_persists_completed_results(
    engine: Engine,
    eval_run_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """execute_eval_run stores per-row metrics and marks the run completed."""
    fixture = Path("data/fixtures/eval/qa_pairs.json").resolve()
    monkeypatch.setenv("VECINITA_EVAL_FIXTURE_PATH", str(fixture))
    run_id = eval_run_id
    with patch(
        "vecinita_internal_write_api.eval_service.run_golden_eval",
        return_value=([_sample_row_result()], _sample_summary()),
    ):
        execute_eval_run(
            engine,
            run_id=run_id,
            corpus_profile="fixture",
            embed_fn=eval_embed_fn,
            judge=MockEvalJudge(),
        )
    detail = get_eval_run(engine, run_id=run_id)
    assert detail is not None
    assert detail.status == "completed"
    assert detail.metrics_summary.retrieval_relevance == pytest.approx(0.91)
    assert len(detail.items) == 1
    assert detail.items[0].metrics.retrieval_pass is True


def test_execute_eval_run_marks_failed_on_exception(
    engine: Engine,
    eval_run_id: str,
) -> None:
    """execute_eval_run sets status failed and re-raises on harness errors."""
    with (
        patch(
            "vecinita_internal_write_api.eval_service.run_golden_eval",
            side_effect=RuntimeError("eval harness failed"),
        ),
        pytest.raises(RuntimeError, match="eval harness failed"),
    ):
        execute_eval_run(
            engine,
            run_id=eval_run_id,
            corpus_profile="fixture",
            embed_fn=eval_embed_fn,
        )
    detail = get_eval_run(engine, run_id=eval_run_id)
    assert detail is not None
    assert detail.status == "failed"


def test_get_eval_run_returns_none_for_missing_id(engine: Engine) -> None:
    """get_eval_run returns None when the run id does not exist."""
    assert get_eval_run(engine, run_id=uuid4()) is None


def test_list_eval_runs_paginates(engine: Engine) -> None:
    """list_eval_runs returns page metadata and ordered items."""
    created_ids: list[object] = []
    min_total_runs = 2
    try:
        created_ids.extend(
            create_eval_run(engine, corpus_profile="fixture").run_id for _ in range(min_total_runs)
        )
        page = list_eval_runs(engine, page=1, page_size=1)
        assert page.page == 1
        assert page.page_size == 1
        assert page.total_count >= min_total_runs
        assert len(page.items) == 1
    finally:
        with engine.begin() as conn:
            for run_id in created_ids:
                conn.execute(
                    text("DELETE FROM eval_run_items WHERE run_id = :id"),
                    {"id": run_id},
                )
                conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})


def test_get_eval_run_parses_non_dict_metrics_and_latency_fallback(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """get_eval_run tolerates malformed metrics JSON and row-level latency."""
    run_id = eval_run_id
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_run_items (
                    run_id, case_id, locale, question, expected_doc_url,
                    retrieved_urls, answer, metrics, latency_ms
                )
                VALUES (
                    :run_id, 'edge-case', 'en', 'Q?', NULL,
                    '[]'::jsonb, NULL, '1'::jsonb, :latency_ms
                )
                """
            ),
            {"run_id": run_id, "latency_ms": _EXPECTED_ROW_LATENCY_MS},
        )
        conn.execute(
            text(
                """
                UPDATE eval_runs
                SET status = 'completed',
                    metrics_summary = CAST(:metrics AS jsonb)
                WHERE id = :id
                """
            ),
            {
                "id": run_id,
                "metrics": json.dumps(
                    {
                        "retrieval_relevance": "bad",
                        "faithfulness": True,
                        "answer_relevancy": 0.5,
                        "latency_p95_ms": 12.9,
                    }
                ),
            },
        )
    detail = get_eval_run(engine, run_id=run_id)
    assert detail is not None
    assert detail.metrics_summary == EvalMetricsSummary(
        retrieval_relevance=None,
        faithfulness=None,
        answer_relevancy=0.5,
        latency_p95_ms=12,
    )
    assert detail.items[0].metrics.latency_ms == _EXPECTED_ROW_LATENCY_MS


def test_execute_eval_run_requires_database_url(
    engine: Engine,
    eval_run_id: UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """execute_eval_run raises when DATABASE_URL is unset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with (
        patch(
            "vecinita_internal_write_api.eval_service.run_golden_eval",
            return_value=([_sample_row_result()], _sample_summary()),
        ),
        pytest.raises(RuntimeError, match="DATABASE_URL is required"),
    ):
        execute_eval_run(
            engine,
            run_id=eval_run_id,
            corpus_profile="staging",
            embed_fn=eval_embed_fn,
        )


def test_default_embed_fn_uses_embedding_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default embed path delegates to EmbeddingClient.embed."""
    monkeypatch.setenv("VECINITA_MODAL_EMBED_URL", "http://embed.test")
    client = MagicMock()
    client.embed.return_value = [0.1, 0.2]
    with patch(
        "vecinita_internal_write_api.eval_service.EmbeddingClient",
        return_value=client,
    ):
        from vecinita_internal_write_api.eval_service import (  # noqa: PLC0415
            _default_embed_fn,  # pyright: ignore[reportPrivateUsage]
        )

        vector = _default_embed_fn("hello")
    assert vector == [0.1, 0.2]
    client.embed.assert_called_once_with("hello")


def test_fixture_path_honors_env_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """VECINITA_EVAL_FIXTURE_PATH overrides the default golden fixture location."""
    fixture = tmp_path / "qa_pairs.json"
    fixture.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("VECINITA_EVAL_FIXTURE_PATH", str(fixture))
    from vecinita_internal_write_api.eval_service import (  # noqa: PLC0415
        _fixture_path,  # pyright: ignore[reportPrivateUsage]
    )

    assert _fixture_path() == fixture


def test_get_eval_run_invalid_status_raises(engine: Engine, eval_run_id: UUID) -> None:
    """Invalid status values in the database are rejected when loading detail."""
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE eval_runs SET status = 'bogus' WHERE id = :id"),
            {"id": eval_run_id},
        )
    with pytest.raises(ValueError, match="invalid eval run status"):
        get_eval_run(engine, run_id=eval_run_id)


def test_list_eval_runs_handles_non_object_metrics_summary(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """list_eval_runs tolerates non-object metrics_summary JSON."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE eval_runs
                SET metrics_summary = '[]'::jsonb
                WHERE id = :id
                """
            ),
            {"id": eval_run_id},
        )
    listed = list_eval_runs(engine, page=1, page_size=20)
    item = next(row for row in listed.items if row.run_id == eval_run_id)
    assert item.metrics_summary == EvalMetricsSummary()


def test_get_eval_run_parses_retrieved_urls_and_metric_latency(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """get_eval_run reads retrieved_urls and float latency_ms from metrics JSON."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_run_items (
                    run_id, case_id, locale, question, expected_doc_url,
                    retrieved_urls, answer, metrics, latency_ms
                )
                VALUES (
                    :run_id, 'latency-case', 'en', 'Q?', NULL,
                    CAST(:urls AS jsonb), 'A', CAST(:metrics AS jsonb), 0
                )
                """
            ),
            {
                "run_id": eval_run_id,
                "urls": json.dumps(["https://example.com/doc"]),
                "metrics": json.dumps(
                    {
                        "retrieval_pass": False,
                        "faithfulness": 0.25,
                        "answer_relevancy": 0.25,
                        "latency_ms": float(_EXPECTED_METRIC_LATENCY_MS) + 0.5,
                    }
                ),
            },
        )
    detail = get_eval_run(engine, run_id=eval_run_id)
    assert detail is not None
    assert detail.items[0].retrieved_urls == ["https://example.com/doc"]
    assert detail.items[0].metrics.retrieval_pass is False
    assert detail.items[0].metrics.latency_ms == _EXPECTED_METRIC_LATENCY_MS


def test_get_eval_run_defaults_latency_when_missing(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """get_eval_run returns zero latency when metrics and row lack timing."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_run_items (
                    run_id, case_id, locale, question, expected_doc_url,
                    retrieved_urls, answer, metrics, latency_ms
                )
                VALUES (
                    :run_id, 'no-latency', 'en', 'Q?', NULL,
                    '1'::jsonb, 'A', '{}'::jsonb, 0
                )
                """
            ),
            {"run_id": eval_run_id},
        )
    detail = get_eval_run(engine, run_id=eval_run_id)
    assert detail is not None
    assert detail.items[0].retrieved_urls == []
    assert detail.items[0].metrics.latency_ms == 0


def test_execute_eval_run_staging_profile_omits_fixture_path(
    engine: Engine,
    eval_run_id: UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Staging corpus_profile does not pass a golden fixture path to the harness."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://vecinita:vecinita@localhost:5432/vecinita",
    )
    with patch(
        "vecinita_internal_write_api.eval_service.run_golden_eval",
        return_value=([_sample_row_result()], _sample_summary()),
    ) as mock_run:
        execute_eval_run(
            engine,
            run_id=eval_run_id,
            corpus_profile="staging",
            embed_fn=eval_embed_fn,
        )
    assert mock_run.call_args.kwargs["fixture_path"] is None


def test_list_eval_runs_parses_optional_timestamps(engine: Engine, eval_run_id: UUID) -> None:
    """list_eval_runs returns started_at/completed_at when present."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE eval_runs
                SET status = 'completed',
                    started_at = now(),
                    completed_at = now(),
                    metrics_summary = '{}'::jsonb
                WHERE id = :id
                """
            ),
            {"id": eval_run_id},
        )
    listed = list_eval_runs(engine, page=1, page_size=20)
    item = next(row for row in listed.items if row.run_id == eval_run_id)
    assert item.started_at is not None
    assert item.completed_at is not None
