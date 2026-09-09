"""Abstain markers accept UX-8 empty-retrieval copy (Bugbot / PR #370)."""

from __future__ import annotations

import pytest
from vecinita_eval.runner import abstain_answer_ok
from vecinita_rag.constants import NO_CONTEXT_MESSAGE_EN, NO_CONTEXT_MESSAGE_ES

pytestmark = pytest.mark.unit


def test_abstain_answer_ok_accepts_ux8_empty_retrieval_copy() -> None:
    """New NO_CONTEXT_MESSAGE EN/ES must count as abstain for golden eval."""
    assert abstain_answer_ok(NO_CONTEXT_MESSAGE_EN) is True
    assert abstain_answer_ok(NO_CONTEXT_MESSAGE_ES) is True


def test_abstain_answer_ok_still_accepts_legacy_markers() -> None:
    """LLM-style abstains that still use legacy phrasing remain OK."""
    assert abstain_answer_ok("I don't have enough information to answer.") is True
    assert abstain_answer_ok("No tengo información suficiente.") is True


def test_abstain_answer_ok_rejects_fabricated_phone() -> None:
    """Phone-like fabricated answers fail abstain even with no-info phrasing."""
    assert abstain_answer_ok("I don't have info but call me at 555-123-4567") is False
