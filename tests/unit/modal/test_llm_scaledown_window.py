"""TC-319-01 / EV-319: prod LLM scaledown_window is import-time env config.

[Corpus: config]
[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-319]
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from infra.modal.llm_app import (
    _scaledown_window_from_env,  # pyright: ignore[reportPrivateUsage]
)

REPO_ROOT = Path(__file__).resolve().parents[3]
LLM_APP = REPO_ROOT / "infra" / "modal" / "llm_app.py"
_ENV_NAME = "VECINITA_LLM_SCALEDOWN_WINDOW"


def test_scaledown_window_defaults_300_when_env_unset() -> None:
    """Unset VECINITA_LLM_SCALEDOWN_WINDOW → 300 (TC-319-01)."""
    with patch.dict(os.environ, {}, clear=True):
        assert _scaledown_window_from_env() == 300


@pytest.mark.parametrize("value", ["60", "120", "300", "600"])
def test_scaledown_window_accepts_valid_bounds(value: str) -> None:
    """Candidates and bounds inclusive 60–600."""
    with patch.dict(os.environ, {_ENV_NAME: value}, clear=True):
        assert _scaledown_window_from_env() == int(value)


@pytest.mark.parametrize("value", ["59", "601", "abc", "12.5", ""])
def test_scaledown_window_rejects_invalid(value: str) -> None:
    """Invalid values fail closed with ValueError."""
    with patch.dict(os.environ, {_ENV_NAME: value}, clear=True), pytest.raises(ValueError):
        _ = _scaledown_window_from_env()


def test_prod_llm_app_wires_scaledown_from_env() -> None:
    """LlmService scaledown_window must use the deploy-import helper."""
    source = LLM_APP.read_text(encoding="utf-8")
    assert "VECINITA_LLM_SCALEDOWN_WINDOW" in source
    assert "_scaledown_window_from_env" in source
    assert "scaledown_window=_PROD_SCALEDOWN_WINDOW" in source
