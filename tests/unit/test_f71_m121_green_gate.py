"""T121.4 — F71 M121 green gate: TC-238-240; F44 not triggered (T121.3 skipped).

[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-238-240]
[Spec: docs/decisions/evolve-decisions.md §S027-D19 / S027-D20 / S027-D39]
"""

from __future__ import annotations

from pathlib import Path

import pytest
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    LEGACY_E0_EMBEDDING_MODEL_ID,
)

_REPO = Path(__file__).resolve().parents[2]
_RUNBOOK = _REPO / "docs" / "staging-runbook.md"
_DECISIONS = _REPO / "docs" / "decisions" / "evolve-decisions.md"


@pytest.mark.unit
def test_tc238_239_240_pins_and_runbook_green() -> None:
    """T121.4: E1/E0 pins distinct; runbook documents prod order + E0 rollback."""
    assert DEFAULT_EMBEDDING_MODEL_ID == "intfloat/multilingual-e5-small"
    assert LEGACY_E0_EMBEDDING_MODEL_ID == "BAAI/bge-small-en-v1.5"
    assert DEFAULT_EMBEDDING_MODEL_ID != LEGACY_E0_EMBEDDING_MODEL_ID
    text = _RUNBOOK.read_text(encoding="utf-8")
    assert "E0 rollback" in text
    assert "Prod cutover" in text
    assert "LEGACY_E0" in text
    assert "BAAI/bge-small-en-v1.5" in text


@pytest.mark.unit
def test_t121_3_f44_tune_not_triggered_this_cycle() -> None:
    """T121.3 skipped: no F44 tune without post-pin F36 ES harm (S027-D39)."""
    decisions = _DECISIONS.read_text(encoding="utf-8")
    lower = decisions.lower()
    assert "S027-D39" in decisions
    assert "F44" in decisions
    assert "not_triggered" in lower or "skipped" in lower
    assert "deferred" in lower
