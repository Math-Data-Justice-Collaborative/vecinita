"""Staging DO FE specs must build from ``stage`` (F83 promote smoke)."""

from __future__ import annotations

from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[3]
_STAGING_FE_SPECS = (
    _ROOT / "infra/do/staging/chat-rag-frontend.yaml",
    _ROOT / "infra/do/staging/data-management-frontend.yaml",
)


def test_staging_frontend_specs_deploy_from_stage_branch() -> None:
    """Promote PR Deploy Staging must build FE from stage, not main.

    Building from ``main`` leaves EnvironmentBanner (and other stage-only UX)
    off live staging FE, so staging-smoke fails on tip-of-stage promote PRs.
    """
    for path in _STAGING_FE_SPECS:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(raw, dict)
        sites = raw.get("static_sites")
        assert isinstance(sites, list) and sites
        github = sites[0].get("github")
        assert isinstance(github, dict)
        assert github.get("branch") == "stage", f"{path.name} github.branch"
        assert github.get("deploy_on_push") is False
