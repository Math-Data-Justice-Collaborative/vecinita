"""Unit tests for F82 output verification + citations (TC-284-TC-287, EV-030)."""

from __future__ import annotations

import pytest
from vecinita_rag.constants import HEDGE_DISCLAIMER_EN, HEDGE_DISCLAIMER_ES
from vecinita_rag.output_verify import (
    FaithfulnessFn,
    OutputVerifyRequest,
    format_inline_citations,
    verify_and_format_answer,
)


def _faithfulness_score(score: float) -> FaithfulnessFn:
    def _fn(**kwargs: object) -> float:
        _ = kwargs
        return score

    return _fn


def test_format_inline_citations_appends_markers_in_order() -> None:
    """TC-287: citation markers map 1..N to sources order."""
    assert format_inline_citations("Food pantry hours vary.", 3) == (
        "Food pantry hours vary. [1][2][3]"
    )


def test_format_inline_citations_skips_when_no_sources() -> None:
    """Empty source list leaves answer unchanged."""
    assert format_inline_citations("Hello.", 0) == "Hello."


def test_format_inline_citations_empty_answer_returns_markers_only() -> None:
    """Whitespace-only answers still emit citation markers."""
    assert format_inline_citations("   ", 2) == "[1][2]"


def test_verify_disabled_returns_answer_unchanged() -> None:
    """TC-286: flag off → no citations or hedge."""
    calls: list[str] = []

    def _judge(**_kwargs: object) -> float:
        calls.append("called")
        return 0.0

    result = verify_and_format_answer(
        OutputVerifyRequest(
            question="Q?",
            answer="Draft answer.",
            context="ctx",
            language="en",
            source_count=2,
            min_score=1.0,
            enabled=False,
            add_citations=True,
        ),
        faithfulness_fn=_judge,
    )
    assert result.answer == "Draft answer."
    assert result.grounded is True
    assert result.faithfulness_score == 1.0
    assert calls == []


def test_verify_grounded_adds_citations_only() -> None:
    """TC-287 / AC-OV3: YES verdict → citations, no hedge."""
    result = verify_and_format_answer(
        OutputVerifyRequest(
            question="Where is food help?",
            answer="Try the RI food bank.",
            context="Food bank at 123 Main.",
            language="en",
            source_count=1,
            min_score=1.0,
            enabled=True,
            add_citations=True,
        ),
        faithfulness_fn=_faithfulness_score(1.0),
    )
    assert result.answer == "Try the RI food bank. [1]"
    assert result.grounded is True
    assert result.faithfulness_score == 1.0


def test_verify_ungrounded_prepends_hedge_en() -> None:
    """TC-285 / AC-OV2: NO verdict → hedge + body + citations."""
    result = verify_and_format_answer(
        OutputVerifyRequest(
            question="Rent help?",
            answer="Call 555-0100 for instant cash.",
            context="No phone numbers in corpus.",
            language="en",
            source_count=2,
            min_score=1.0,
            enabled=True,
            add_citations=True,
        ),
        faithfulness_fn=_faithfulness_score(0.0),
    )
    assert result.answer.startswith(HEDGE_DISCLAIMER_EN)
    assert "Call 555-0100 for instant cash." in result.answer
    assert result.answer.endswith("[1][2]")
    assert result.grounded is False
    assert result.faithfulness_score == 0.0


def test_verify_ungrounded_prepends_hedge_es() -> None:
    """TC-285: Spanish hedge disclaimer on ungrounded verdict."""
    result = verify_and_format_answer(
        OutputVerifyRequest(
            question="¿Ayuda de alquiler?",
            answer="Llame al 555-0100.",
            context="Sin teléfonos.",
            language="es",
            source_count=1,
            min_score=1.0,
            enabled=True,
            add_citations=True,
        ),
        faithfulness_fn=_faithfulness_score(0.0),
    )
    assert result.answer.startswith(HEDGE_DISCLAIMER_ES)


@pytest.mark.parametrize("score", [0.5, 0.99])
def test_verify_respects_min_score_threshold(score: float) -> None:
    """Scores below min_score are treated as ungrounded."""
    result = verify_and_format_answer(
        OutputVerifyRequest(
            question="Q?",
            answer="Maybe.",
            context="ctx",
            language="en",
            source_count=1,
            min_score=1.0,
            enabled=True,
            add_citations=False,
        ),
        faithfulness_fn=_faithfulness_score(score),
    )
    assert result.grounded is False
