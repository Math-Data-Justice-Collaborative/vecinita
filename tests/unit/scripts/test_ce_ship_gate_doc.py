"""Unit test for F45 CE ship-gate report (T98.3 / TC-184; EV-018 filled)."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_S020 = _ROOT / "docs" / "sessions" / "S020-retrieval-batch-b" / "reports" / "ce-ship-gate.md"
_S021 = _ROOT / "docs" / "sessions" / "S021-retrieval-follow-on" / "reports" / "ce-ship-gate.md"


def test_ce_ship_gate_template_documents_floors_and_metrics_path() -> None:
    """Ship-gate docs cite floors, metrics JSON, prod LLM constraint, and pass evidence."""
    text = _S020.read_text(encoding="utf-8")
    assert "0.28" in text
    assert "0.91" in text
    assert "BAAI/bge-reranker-v2-m3" in text
    assert "spike-f45-ce-ship-gate.json" in text
    assert "VECINITA_MODAL_LLM_URL" in text
    assert "ship_gate_pass" in text
    # EV-018 T100.1 filled the S020 Path A template; S021 holds the re-gate narrative.
    assert "PASS" in text
    assert _S021.is_file()
    s021 = _S021.read_text(encoding="utf-8")
    assert "ship_gate_pass" in s021
    assert "0.778" in s021 or "0.28" in s021
