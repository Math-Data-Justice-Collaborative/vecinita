"""T121.1 red — TC-240 staging-then-prod + E0 rollback runbook markers (AC-ME6/ME10).

Fails until T121.2 adds the prod cutover / E0 rollback section to staging-runbook.md.

[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-240]
[Spec: docs/acceptance-criteria.md §AC-ME6]
[Spec: docs/decisions/evolve-decisions.md §S027-D21 / S027-D22]
"""

from __future__ import annotations

from pathlib import Path

import pytest

_RUNBOOK = Path(__file__).resolve().parents[2] / "docs" / "staging-runbook.md"


@pytest.mark.unit
def test_tc240_staging_runbook_documents_staging_then_prod_and_e0_rollback() -> None:
    """TC-240 / AC-ME6: runbook must order staging cutover before prod + E0 rollback."""
    text = _RUNBOOK.read_text(encoding="utf-8")
    assert "staging first" in text.lower() or "Staging first" in text
    # Prod repeat after staging promote (S027-D21)
    assert "repeat" in text.lower() and "prod" in text.lower()
    # Explicit E0 rollback procedure (S027-D22 / AC-ME9) — T121.2
    assert "E0 rollback" in text or "rollback to E0" in text.lower()
    assert "LEGACY_E0" in text or "BAAI/bge-small-en-v1.5" in text
    assert "new" in text.lower() and "rebuild" in text.lower()
    # Operator promote abort = judgment (S027-D11)
    assert "operator judgment" in text.lower() or "no hard numeric" in text.lower()
