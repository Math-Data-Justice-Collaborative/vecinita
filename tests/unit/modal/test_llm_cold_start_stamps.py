"""TC-314: restore path emits cold_start_stamp (source contract)."""

from __future__ import annotations

from pathlib import Path

_CORE = Path(__file__).resolve().parents[3] / "infra" / "modal" / "llm_service_core.py"


def test_snapshot_restore_emits_cold_start_stamp() -> None:
    """Modal-only stamps: restore → wake/adapter_ready + generate first_token."""
    source = _CORE.read_text(encoding="utf-8")
    assert "validate_cold_start_sample" in source
    assert 'cold_kind": "snapshot_restore"' in source or 'cold_kind": "snapshot_restore"' in source
    assert "cold_start_stamp" in source
    assert "first_token_ms" in source
