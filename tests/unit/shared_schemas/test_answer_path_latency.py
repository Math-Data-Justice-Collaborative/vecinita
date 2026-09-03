"""TC-320-05: harness records answer_path without overloading cold_kind (AC-320-05)."""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.cold_start_latency import (
    AnswerPathColdKindConflictError,
    ForbiddenColdStartTagError,
    UnknownAnswerPathSampleError,
    summarize_by_answer_path,
    validate_answer_path_latency_sample,
)

_FAQ_N = 2
_RAG_N = 3


def test_validate_answer_path_sample_accepts_faq_bypass() -> None:
    """FAQ samples stamp answer_path only — not GPU cold_kind (ADR-022 EV-320)."""
    sample = validate_answer_path_latency_sample(
        {
            "answer_path": "faq_bypass",
            "event": "chat_ask",
            "first_token_ms": 12.5,
        }
    )
    assert sample == {
        "answer_path": "faq_bypass",
        "event": "chat_ask",
        "first_token_ms": 12.5,
    }
    assert "cold_kind" not in sample


def test_validate_answer_path_sample_accepts_rag_llm() -> None:
    """ChatRAG miss / kill-switch path can be timed with answer_path=rag_llm."""
    sample = validate_answer_path_latency_sample(
        {"answer_path": "rag_llm", "first_token_ms": 900.0}
    )
    assert sample["answer_path"] == "rag_llm"
    assert sample.get("first_token_ms") == pytest.approx(900.0)


def test_validate_answer_path_sample_rejects_cold_kind_on_faq_bypass() -> None:
    """Do not overload warm/snapshot_* as FAQ (domain-vocabulary / ADR-022)."""
    with pytest.raises(AnswerPathColdKindConflictError) as exc:
        _ = validate_answer_path_latency_sample(
            {
                "answer_path": "faq_bypass",
                "cold_kind": "warm",
                "first_token_ms": 1.0,
            }
        )
    assert "cold_kind" in str(exc.value)
    assert "faq_bypass" in str(exc.value)


def test_validate_answer_path_sample_rejects_prompt_keys() -> None:
    """ADR-004 — never persist question/answer text in harness tags."""
    with pytest.raises(ForbiddenColdStartTagError) as exc:
        _ = validate_answer_path_latency_sample(
            {"answer_path": "faq_bypass", "question": "What is Vecinita?"}
        )
    assert "question" in str(exc.value)


def test_validate_answer_path_sample_rejects_unknown_path() -> None:
    """Fail closed on non-allow-listed answer_path."""
    with pytest.raises(UnknownAnswerPathSampleError):
        _ = validate_answer_path_latency_sample(
            {"answer_path": "snapshot_restore", "first_token_ms": 1.0}
        )


def test_summarize_by_answer_path_groups_faq_and_rag() -> None:
    """Layer E dashboard breakdown: faq_bypass vs rag_llm percentiles."""
    samples: list[dict[str, object]] = [
        {"answer_path": "faq_bypass", "first_token_ms": 10.0},
        {"answer_path": "faq_bypass", "first_token_ms": 20.0},
        {"answer_path": "rag_llm", "first_token_ms": 100.0},
        {"answer_path": "rag_llm", "first_token_ms": 200.0},
        {"answer_path": "rag_llm", "first_token_ms": 300.0},
    ]
    summary = summarize_by_answer_path(samples)
    assert summary["faq_bypass"] == {
        "n": _FAQ_N,
        "p50_ms": 15.0,
        "p95_ms": pytest.approx(19.5),
    }
    assert summary["rag_llm"]["n"] == _RAG_N
    assert summary["rag_llm"]["p50_ms"] == pytest.approx(200.0)
