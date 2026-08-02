"""Unit test for EV-017 Phase 22 gate checklist doc (T98.4)."""

from __future__ import annotations

from pathlib import Path

_DOC = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S020-retrieval-batch-b"
    / "reports"
    / "phase22-gate-checklist.md"
)


def test_phase22_gate_checklist_links_adr042_and_ce_docs() -> None:
    """Gate checklist references ADR-042, CE ship-gate, and T2 pass."""
    text = _DOC.read_text(encoding="utf-8")
    assert "ADR-042" in text
    assert "ce-ship-gate.md" in text
    assert "PASS at T2" in text
    assert "08-verify-build" in text
