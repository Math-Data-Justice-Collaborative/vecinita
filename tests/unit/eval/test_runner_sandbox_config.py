"""Sandbox config override wiring for eval runner (F37, T68.7)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest
from vecinita_eval.golden import load_golden_rows
from vecinita_eval.runner import run_adhoc_eval, run_golden_eval
from vecinita_eval.sandbox import synthesize_with_system_prompt
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import EvalConfig

from tests.helpers.eval_judge import MockEvalJudge

pytestmark = pytest.mark.unit

_FIXTURE_PATH = Path(__file__).resolve().parents[3] / "data/fixtures/eval/qa_pairs.json"
_UNUSED_DB = "postgresql+psycopg://unused"
_OVERRIDE_TOP_K = 3
_OVERRIDE_MIN_SCORE = 0.75
_DEFAULT_TOP_K = 5
_DEFAULT_SCORE_THRESHOLD = 0.5


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


class _RecordingLLM:
    """Capture synthesis prompts for sandbox system_prompt assertions."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(
        self,
        prompt: str,
        *,
        formatted: bool = False,
        **kwargs: object,
    ) -> object:
        _ = (formatted, kwargs)
        self.prompts.append(prompt)
        return type("Resp", (), {"text": "Sandbox answer."})()


def test_run_golden_eval_applies_top_k_and_min_retrieval_score() -> None:
    """Sandbox config overrides retriever top_k and score_threshold."""
    config = EvalConfig(top_k=_OVERRIDE_TOP_K, min_retrieval_score=_OVERRIDE_MIN_SCORE)
    with (
        patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[]),
        patch.object(CorpusPgvectorRetriever, "__init__", autospec=True) as mock_init,
    ):
        mock_init.return_value = None
        run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=None,
            llm=None,
            fixture_path=_FIXTURE_PATH,
            config=config,
        )
    kwargs = mock_init.call_args.kwargs
    assert kwargs["top_k"] == _OVERRIDE_TOP_K
    assert kwargs["score_threshold"] == pytest.approx(_OVERRIDE_MIN_SCORE)


def test_run_golden_eval_uses_sandbox_system_prompt_for_synthesis() -> None:
    """Sandbox system_prompt is injected into LLM synthesis."""
    config = EvalConfig(system_prompt="Use only the provided context. Be brief.")
    llm = _RecordingLLM()
    chunk = _sample_chunk()
    with patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[chunk]):
        run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=None,
            llm=llm,  # pyright: ignore[reportArgumentType]
            fixture_path=_FIXTURE_PATH,
            config=config,
        )
    assert llm.prompts
    assert llm.prompts[0].startswith("Use only the provided context. Be brief.")


def test_run_adhoc_eval_returns_single_row_with_question() -> None:
    """Ad-hoc mode evaluates one operator question through sandbox RAG + judge."""
    judge = MockEvalJudge(faithfulness_score=0.81, answer_relevancy_score=0.77)
    chunk = _sample_chunk()
    question = "When are food pantry hours updated?"
    with patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[chunk]):
        results, summary = run_adhoc_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=judge,
            llm=None,
            question=question,
            config=EvalConfig(top_k=4),
        )
    assert len(results) == 1
    row = results[0]
    assert row.row.id == "adhoc"
    assert row.row.question == question
    assert row.retrieved_urls == [chunk.url]
    assert row.metrics.faithfulness == pytest.approx(0.81)
    assert row.metrics.answer_relevancy == pytest.approx(0.77)
    assert summary.retrieval_relevance == pytest.approx(1.0)


def test_synthesize_with_system_prompt_includes_context_and_question() -> None:
    """Sandbox synthesis prompt includes system rules, context, and question."""
    llm = _RecordingLLM()
    chunk = _sample_chunk()
    answer = synthesize_with_system_prompt(
        "What are pantry hours?",
        [chunk],
        llm,  # pyright: ignore[reportArgumentType]
        system_prompt="Answer from context only.",
    )
    assert answer.answer == "Sandbox answer."
    assert "Answer from context only." in llm.prompts[0]
    assert chunk.text in llm.prompts[0]
    assert "What are pantry hours?" in llm.prompts[0]


def test_run_golden_eval_without_config_keeps_default_retriever_params() -> None:
    """Backward-compatible default top_k when no sandbox config is supplied."""
    with (
        patch.object(CorpusPgvectorRetriever, "retrieve_chunks", return_value=[]),
        patch.object(CorpusPgvectorRetriever, "__init__", autospec=True) as mock_init,
    ):
        mock_init.return_value = None
        rows = load_golden_rows(fixture_path=_FIXTURE_PATH)
        run_golden_eval(
            embed_fn=_stub_embed_fn,
            database_url=_UNUSED_DB,
            judge=None,
            llm=None,
            fixture_path=_FIXTURE_PATH,
        )
    kwargs = mock_init.call_args.kwargs
    assert kwargs["top_k"] == _DEFAULT_TOP_K
    assert kwargs["score_threshold"] == pytest.approx(_DEFAULT_SCORE_THRESHOLD)
    assert rows
