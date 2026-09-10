"""EV-354 / #354: staging idle posture docs + embed default (TC-325, TC-327).

[Corpus: staging]
[Corpus: feature-list.md §F83]
[Spec: docs/test-plan.md §TC-325]
[Spec: docs/test-plan.md §TC-327]
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs" / "staging-runbook.md"
SECRETS = REPO_ROOT / "docs" / "staging-secrets-matrix.md"
CONFIG = REPO_ROOT / "docs" / "config-spec.md"
ACCEPT = REPO_ROOT / "docs" / "acceptance-criteria.md"


def test_tc325_staging_embed_min_containers_documented_as_zero() -> None:
    """AC-ST9: staging idle posture requires embed min_containers=0."""
    runbook = RUNBOOK.read_text(encoding="utf-8")
    secrets = SECRETS.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    accept = ACCEPT.read_text(encoding="utf-8")

    assert "VECINITA_EMBED_MIN_CONTAINERS" in runbook
    assert "VECINITA_EMBED_MIN_CONTAINERS=0" in runbook or "`0`" in runbook
    assert "AC-ST9" in accept
    assert "VECINITA_EMBED_MIN_CONTAINERS" in secrets
    assert "**`0`**" in secrets or "`0`" in secrets
    assert "Staging must stay 0" in config or "staging must stay 0" in config.lower()


def test_tc327_obs_droplet_default_powered_off_in_runbook() -> None:
    """AC-ST11: obs droplet default cost posture is powered off."""
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "Idle cost posture" in text or "idle cost posture" in text.lower()
    assert "powered off" in text.lower()
    assert "vecinita-staging-obs" in text
    assert "AC-ST11" in text or "EV-323-D13" in text
