"""BUG-2026-07-01: eval runs leave faithfulness/answer_relevancy null without wired judge."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from vecinita_eval.modal_llm import default_eval_runtime
from vecinita_eval.runner import EvalSummary
from vecinita_internal_write_api.eval_service import create_eval_run, execute_eval_run

from tests.eval.conftest import eval_embed_fn

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.unit


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    """SQLAlchemy engine for eval persistence tests."""
    monkeypatch.setenv("DATABASE_URL", _database_url())
    eng = create_engine(_database_url())
    yield eng
    eng.dispose()


def test_execute_eval_run_wires_default_judge_and_llm_when_modal_url_set(
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Factory eval path must pass judge + LLM when VECINITA_MODAL_LLM_URL is configured."""
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")
    created = create_eval_run(engine, corpus_profile="fixture")
    run_id = created.run_id
    summary = EvalSummary(
        retrieval_relevance=0.5,
        faithfulness=0.75,
        answer_relevancy=0.72,
        latency_p95_ms=500,
    )
    try:
        with patch(
            "vecinita_internal_write_api.eval_service.run_golden_eval",
            return_value=([], summary),
        ) as mock_run:
            execute_eval_run(
                engine,
                run_id=run_id,
                corpus_profile="fixture",
                embed_fn=eval_embed_fn,
            )

        kwargs = mock_run.call_args.kwargs
        assert kwargs["judge"] is not None
        assert kwargs["llm"] is not None
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})


def test_default_eval_runtime_returns_none_without_modal_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing VECINITA_MODAL_LLM_URL keeps prior behavior (no judge/LLM)."""
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)
    judge, llm = default_eval_runtime()
    assert judge is None
    assert llm is None
