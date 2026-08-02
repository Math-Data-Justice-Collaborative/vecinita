"""Unit tests for EV-017 F45 CE spike runbook + metrics path (T97.5 / TC-184)."""

from __future__ import annotations

from pathlib import Path

_RUNBOOK = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S020-retrieval-batch-b"
    / "reports"
    / "spike-f45-ce-runbook.md"
)
_METRICS_JSON = "docs/sessions/S020-retrieval-batch-b/reports/spike-f45-ce-ship-gate.json"
_HARNESS = "docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_ship_gate.py"
_MODAL = "docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_modal.py"
_CE_MODEL = "BAAI/bge-reranker-v2-m3"
_RELEVANCY = "0.28"
_FAITH = "0.91"


def test_f45_ce_runbook_documents_metrics_path_and_floors() -> None:
    """Runbook points at harness, metrics JSON, model pin, and TC-184 floors."""
    text = _RUNBOOK.read_text(encoding="utf-8")
    assert _HARNESS in text
    assert _MODAL in text
    assert _METRICS_JSON in text
    assert _CE_MODEL in text
    assert _RELEVANCY in text
    assert _FAITH in text
    assert "VECINITA_MODAL_LLM_URL" in text
    assert "VECINITA_MODAL_LLM_PLAYGROUND_URL" in text
    assert "ship_gate_pass" in text
