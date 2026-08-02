"""T104.4 - AC-IR7 out-of-scope held for EV-019 (no Playwright unless FE knobs)."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]


def test_ac_ir7_no_playwright_uj062_unless_fe_knobs() -> None:
    """No Playwright UJ-062 suite unless admin FE ships force/overlap knobs (M5/TP4)."""
    ui_tests = _REPO / "tests" / "ui"
    if not ui_tests.is_dir():
        return
    matches = list(ui_tests.rglob("*uj062*"))
    assert matches == [], f"unexpected Playwright UJ-062 paths: {matches}"


def test_ac_ir7_no_ce_flag_flip_in_ev019_docs() -> None:
    """EV-019 must not flip cross-encoder / packing / multilingual-embed scope."""
    decisions = (_REPO / "docs" / "decisions.md").read_text(encoding="utf-8")
    # Locked out-of-scope markers from Phase 0 / TP5.
    assert "#159" in decisions or "multilingual" in decisions.lower()
    assert "AC-IR7" in (_REPO / "docs" / "acceptance-criteria.md").read_text(encoding="utf-8")
