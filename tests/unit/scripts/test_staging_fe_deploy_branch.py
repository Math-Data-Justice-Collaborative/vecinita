"""Staging DO specs must build from ``stage`` (F83 promote smoke)."""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_STAGING_FE_SPECS = (
    _ROOT / "infra/do/staging/chat-rag-frontend.yaml",
    _ROOT / "infra/do/staging/data-management-frontend.yaml",
)
_STAGING_BACKEND_SPECS = (
    _ROOT / "infra/do/staging/chat-rag-backend.yaml",
    _ROOT / "infra/do/staging/internal-write-api.yaml",
)
_BRANCH_RE = re.compile(
    r"github:\s*\n(?:[ \t]+.+\n)*?[ \t]+branch:\s*(\S+)",
    re.MULTILINE,
)


def test_staging_frontend_specs_deploy_from_stage_branch() -> None:
    """Promote PR Deploy Staging must build FE from stage, not main.

    Building from ``main`` leaves EnvironmentBanner (and other stage-only UX)
    off live staging FE, so staging-smoke fails on tip-of-stage promote PRs.
    """
    for path in _STAGING_FE_SPECS:
        text = path.read_text(encoding="utf-8")
        match = _BRANCH_RE.search(text)
        assert match is not None, f"{path.name}: missing github.branch"
        assert match.group(1) == "stage", f"{path.name} github.branch"
        assert "deploy_on_push: false" in text


def test_staging_backend_specs_deploy_from_stage_branch() -> None:
    """Promote PR Deploy Staging must build ChatRAG/write API from stage.

    Building backends from ``main`` leaves OpenAPI requestBody publishers
    (TC-332/TC-336) and other tip-of-stage API contracts off live staging,
    so staging-smoke fails on stage→main promote PRs even when CI is green.
    [Corpus: feature-list.md §F83] [Corpus: staging]
    """
    for path in _STAGING_BACKEND_SPECS:
        text = path.read_text(encoding="utf-8")
        match = _BRANCH_RE.search(text)
        assert match is not None, f"{path.name}: missing github.branch"
        assert match.group(1) == "stage", f"{path.name} github.branch"
        assert "deploy_on_push: false" in text
