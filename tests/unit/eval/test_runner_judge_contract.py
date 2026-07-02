"""Runner judge contract — prevents null faithfulness/answer_relevancy regressions (F36, TC-112)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest
from vecinita_eval.runner import run_golden_eval
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RetrievedChunk

from tests.helpers.eval_judge import MockEvalJudge

pytestmark = pytest.mark.unit

_FIXTURE_PATH = Path(__file__).resolve().parents[3] / "data/fixtures/eval/qa_pairs.json"
_UNUSED_DB = "postgresql+psycopg://unused"


def _stub_embed_fn(_question: str) -> list[float]:
    return [0.0] * 384


def _sample_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=UUID("00000000-0000-0000-0000-000000000001"),
        document_id=UUID("00000000-0000-0000-0000-000000000002"),
        text="Food pantry hours are posted weekly on the community board.",
        score=0.92,
        title="Community resources",
        url="fixture://corpus/en/community-resources.md",
        language="en",
    )


def test_run_golden_eval_without_judge_leaves_quality_metrics_null() -> None:
    """TC-112 guard: no judge client → faithfulness and answer relevancy stay null."""
    with patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[]):
        results, summary = run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=None,
            llm=None,
            fixture_path=_FIXTURE_PATH,
        )
    assert results
    assert all(row.metrics.faithfulness is None for row in results)
    assert all(row.metrics.answer_relevancy is None for row in results)
    assert summary.faithfulness is None
    assert summary.answer_relevancy is None


def test_run_golden_eval_scores_answer_relevancy_without_retrieved_chunks() -> None:
    """TC-112 guard: LlamaIndex answer relevancy runs even when pgvector returns nothing."""
    judge = MockEvalJudge(answer_relevancy_score=0.71)
    with patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[]):
        results, summary = run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=judge,
            llm=None,
            fixture_path=_FIXTURE_PATH,
        )
    assert results
    assert all(row.metrics.answer_relevancy == pytest.approx(0.71) for row in results)
    assert all(row.metrics.faithfulness is None for row in results)
    assert summary.answer_relevancy == pytest.approx(0.71)
    assert summary.faithfulness is None


def test_run_golden_eval_faithfulness_requires_retrieved_context() -> None:
    """TC-112 guard: faithfulness stays null without chunks even when judge is wired."""
    judge = MockEvalJudge(faithfulness_score=0.88, answer_relevancy_score=0.75)
    with patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[]):
        results, _summary = run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=judge,
            llm=None,
            fixture_path=_FIXTURE_PATH,
        )
    hit_rows = [row for row in results if row.row.retrieval_expectation == "hit"]
    assert hit_rows
    assert all(row.metrics.faithfulness is None for row in hit_rows)
    assert all(row.metrics.answer_relevancy == pytest.approx(0.75) for row in hit_rows)


def test_run_golden_eval_scores_faithfulness_when_chunks_present() -> None:
    """TC-112 guard: faithfulness is populated when judge is wired and context exists."""
    judge = MockEvalJudge(faithfulness_score=0.82, answer_relevancy_score=0.79)
    chunk = _sample_chunk()
    with patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[chunk]):
        results, summary = run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=judge,
            llm=None,
            fixture_path=_FIXTURE_PATH,
        )
    food_pantry = next(
        row for row in results if row.row.id == "community-food-pantry" and row.row.locale == "en"
    )
    assert food_pantry.metrics.faithfulness == pytest.approx(0.82)
    assert food_pantry.metrics.answer_relevancy == pytest.approx(0.79)
    assert summary.faithfulness == pytest.approx(0.82)
    assert summary.answer_relevancy == pytest.approx(0.79)


def test_run_golden_eval_abstain_rows_skip_faithfulness_but_score_answer_relevancy() -> None:
    """TC-113 guard: abstain rows never get faithfulness; answer relevancy still runs."""
    judge = MockEvalJudge(faithfulness_score=0.9, answer_relevancy_score=0.65)
    chunk = _sample_chunk()
    with patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[chunk]):
        results, _summary = run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=judge,
            llm=None,
            fixture_path=_FIXTURE_PATH,
        )
    abstain = next(row for row in results if row.row.id == "edge-abstain-mayor-phone")
    assert abstain.metrics.faithfulness is None
    assert abstain.metrics.answer_relevancy == pytest.approx(0.65)
