"""Unit test for EV-017 F45 CE ship-gate report template (T98.3 / TC-184)."""

from __future__ import annotations

from pathlib import Path

_DOC = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S020-retrieval-batch-b"
    / "reports"
    / "ce-ship-gate.md"
)


def test_ce_ship_gate_template_documents_floors_and_metrics_path() -> None:
    """Ship-gate template cites floors, metrics JSON, and prod LLM constraint."""
    text = _DOC.read_text(encoding="utf-8")
    assert "0.28" in text
    assert "0.91" in text
    assert "BAAI/bge-reranker-v2-m3" in text
    assert "spike-f45-ce-ship-gate.json" in text
    assert "VECINITA_MODAL_LLM_URL" in text
    assert "ship_gate_pass" in text
    assert "PENDING" in text
