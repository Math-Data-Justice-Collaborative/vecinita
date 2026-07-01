"""Unit tests for eval run persistence and execution (F36, ADR-033)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Self, cast
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from vecinita_eval.golden import GoldenRow
from vecinita_eval.runner import EvalSummary, RowMetrics, RowResult
from vecinita_internal_write_api.eval_service import (
    create_eval_run,
    execute_eval_run,
    get_eval_run,
    get_eval_timeseries,
    list_eval_runs,
)
from vecinita_shared_schemas.internal_write import EvalMetricsSummary

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

_EXPECTED_ROW_LATENCY_MS = 1500
_EXPECTED_METRIC_LATENCY_MS = 99
_EXPECTED_LATENCY_P95_MS = 12


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
        custom_scores={"tone-friendly": 0.88},
    )


@pytest.fixture
def eval_run_id(engine: Engine) -> Iterator[UUID]:
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
    eval_run_id: UUID,
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
    with engine.connect() as conn:
        row = cast(
            dict[str, object],
            conn.execute(
                text("SELECT metrics_summary FROM eval_runs WHERE id = :id"),
                {"id": run_id},
            ).scalar_one(),
        )
    assert row.get("custom_scores") == {"tone-friendly": 0.88}


def test_execute_eval_run_marks_failed_on_exception(
    engine: Engine,
    eval_run_id: UUID,
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

    class StubEmbeddingClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def embed(self, text: str) -> list[float]:
            self.calls.append(text)
            return [0.1, 0.2]

    stub = StubEmbeddingClient()
    with patch(
        "vecinita_internal_write_api.eval_service.EmbeddingClient",
        return_value=stub,
    ):
        from vecinita_internal_write_api.eval_service import (  # noqa: PLC0415
            _default_embed_fn,  # pyright: ignore[reportPrivateUsage]
        )

        vector = _default_embed_fn("hello")
    assert vector == [0.1, 0.2]
    assert stub.calls == ["hello"]


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


def test_fixture_path_falls_back_to_repo_root_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Relative fixture paths resolve under the repository root when not absolute files."""
    monkeypatch.setenv("VECINITA_EVAL_FIXTURE_PATH", "data/fixtures/eval/missing.json")
    from vecinita_internal_write_api.eval_service import (  # noqa: PLC0415
        _fixture_path,  # pyright: ignore[reportPrivateUsage]
    )

    path = _fixture_path()
    assert path.as_posix().endswith("data/fixtures/eval/missing.json")


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


def test_get_eval_timeseries_returns_completed_points(engine: Engine, eval_run_id: UUID) -> None:
    """get_eval_timeseries lists completed runs with builtin and custom metrics."""
    completed_at = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE eval_runs
                SET status = 'completed',
                    started_at = :completed_at,
                    completed_at = :completed_at,
                    metrics_summary = CAST(:metrics AS jsonb)
                WHERE id = :id
                """
            ),
            {
                "id": eval_run_id,
                "completed_at": completed_at,
                "metrics": json.dumps(
                    {
                        "retrieval_relevance": 0.9,
                        "faithfulness": 0.8,
                        "answer_relevancy": 0.7,
                        "latency_p95_ms": 1000,
                        "custom_scores": {"tone-friendly": 0.85},
                    }
                ),
            },
        )
    series = get_eval_timeseries(engine, limit=100)
    matching = [point for point in series.points if point.run_id == eval_run_id]
    assert len(matching) == 1
    assert matching[0].metrics_summary.custom_scores == {"tone-friendly": 0.85}
    assert "tone-friendly" in series.available_metrics


def test_get_eval_timeseries_skips_rows_without_completed_at(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """get_eval_timeseries ignores completed runs missing completed_at."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE eval_runs
                SET status = 'completed',
                    completed_at = NULL,
                    metrics_summary = '{}'::jsonb
                WHERE id = :id
                """
            ),
            {"id": eval_run_id},
        )
    series = get_eval_timeseries(engine, limit=10)
    assert all(point.run_id != eval_run_id for point in series.points)


def test_get_eval_run_parses_custom_scores_and_skips_invalid_entries(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """get_eval_run keeps valid custom score entries and drops invalid values."""
    with engine.begin() as conn:
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
                "id": eval_run_id,
                "metrics": json.dumps(
                    {
                        "custom_scores": {
                            "good": 0.8,
                            "bad": True,
                        },
                        "latency_p95_ms": 12.5,
                    }
                ),
            },
        )
    detail = get_eval_run(engine, run_id=eval_run_id)
    assert detail is not None
    assert detail.metrics_summary.custom_scores == {"good": 0.8}
    assert detail.metrics_summary.latency_p95_ms == _EXPECTED_LATENCY_P95_MS


def test_execute_eval_run_omits_custom_scores_when_empty(
    engine: Engine,
    eval_run_id: UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_summary_to_json skips custom_scores when the harness returns none."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://vecinita:vecinita@localhost:5432/vecinita",
    )
    summary = EvalSummary(
        retrieval_relevance=0.5,
        faithfulness=0.5,
        answer_relevancy=0.5,
        latency_p95_ms=100,
        custom_scores=None,
    )
    with patch(
        "vecinita_internal_write_api.eval_service.run_golden_eval",
        return_value=([_sample_row_result()], summary),
    ):
        execute_eval_run(
            engine,
            run_id=eval_run_id,
            corpus_profile="fixture",
            embed_fn=eval_embed_fn,
        )
    with engine.connect() as conn:
        row = cast(
            dict[str, object],
            conn.execute(
                text("SELECT metrics_summary FROM eval_runs WHERE id = :id"),
                {"id": eval_run_id},
            ).scalar_one(),
        )
    assert "custom_scores" not in row


def test_optional_int_returns_none_for_bool() -> None:
    """_optional_int rejects boolean values."""
    from vecinita_internal_write_api.eval_service import (  # noqa: PLC0415
        _optional_int,  # pyright: ignore[reportPrivateUsage]
    )

    assert _optional_int(value=True) is None


def test_create_eval_run_fallback_created_at(
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_eval_run uses UTC now when created_at is not a datetime."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://vecinita:vecinita@localhost:5432/vecinita",
    )
    with patch(
        "vecinita_internal_write_api.eval_service.sqlalchemy_scalar_one",
        return_value="not-a-datetime",
    ):
        created = create_eval_run(engine, corpus_profile="fixture")
    try:
        assert created.created_at.tzinfo is UTC
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": created.run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": created.run_id})


def test_latency_ms_defaults_when_item_latency_is_float(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """_latency_ms returns zero when only a float row latency is present."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_run_items (
                    run_id, case_id, locale, question, expected_doc_url,
                    retrieved_urls, answer, metrics, latency_ms
                )
                VALUES (
                    :run_id, 'float-latency', 'en', 'Q?', NULL,
                    '[]'::jsonb, 'A', '{}'::jsonb, 0
                )
                """
            ),
            {"run_id": eval_run_id},
        )
        conn.execute(
            text(
                """
                UPDATE eval_run_items
                SET metrics = CAST(:metrics AS jsonb),
                    latency_ms = 0
                WHERE run_id = :run_id AND case_id = 'float-latency'
                """
            ),
            {
                "run_id": eval_run_id,
                "metrics": json.dumps({}),
            },
        )
    from vecinita_internal_write_api.eval_service import (  # noqa: PLC0415
        _latency_ms,  # pyright: ignore[reportPrivateUsage]
    )

    item: dict[str, object] = {"latency_ms": 12.5}
    assert _latency_ms(item, {}) == 0


def test_get_eval_timeseries_skips_non_datetime_completed_at() -> None:
    """get_eval_timeseries ignores rows whose completed_at is not a datetime."""
    fake_row: dict[str, object] = {
        "id": uuid4(),
        "completed_at": "2026-01-01T00:00:00Z",
        "metrics_summary": {},
    }

    class FakeResult:
        def mappings(self) -> FakeResult:
            return self

        def all(self) -> list[dict[str, object]]:
            return [fake_row]

    class FakeConn:
        def execute(self, *_args: object, **_kwargs: object) -> FakeResult:
            return FakeResult()

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    class FakeEngine:
        def connect(self) -> FakeConn:
            return FakeConn()

    series = get_eval_timeseries(FakeEngine(), limit=10)  # type: ignore[arg-type]
    assert series.points == []


def test_get_eval_run_optional_int_bool_latency_p95(
    engine: Engine,
    eval_run_id: UUID,
) -> None:
    """get_eval_run drops boolean latency_p95_ms values."""
    with engine.begin() as conn:
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
                "id": eval_run_id,
                "metrics": json.dumps({"latency_p95_ms": True}),
            },
        )
    detail = get_eval_run(engine, run_id=eval_run_id)
    assert detail is not None
    assert detail.metrics_summary.latency_p95_ms is None
