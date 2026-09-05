"""EV-323 / #323: embedding ASGI min_containers is deploy-import env config.

[Corpus: config]
[Corpus: ADR-004]
[Spec: docs/config-spec.md §VECINITA_EMBED_MIN_CONTAINERS]
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from infra.modal.embedding_app import (
    _embed_min_containers_from_env,  # pyright: ignore[reportPrivateUsage]
)

REPO_ROOT = Path(__file__).resolve().parents[3]
EMBED_APP = REPO_ROOT / "infra" / "modal" / "embedding_app.py"
_ENV_NAME = "VECINITA_EMBED_MIN_CONTAINERS"


def test_embed_min_containers_defaults_0_when_env_unset() -> None:
    """Unset VECINITA_EMBED_MIN_CONTAINERS → 0 (scale-to-zero / ADR-004)."""
    with patch.dict(os.environ, {}, clear=True):
        assert _embed_min_containers_from_env() == 0


@pytest.mark.parametrize("value", ["0", "1"])
def test_embed_min_containers_accepts_0_or_1(value: str) -> None:
    """Only {0, 1} are valid (config-spec)."""
    with patch.dict(os.environ, {_ENV_NAME: value}, clear=True):
        assert _embed_min_containers_from_env() == int(value)


@pytest.mark.parametrize("value", ["2", "-1", "abc", "1.5", ""])
def test_embed_min_containers_rejects_invalid(value: str) -> None:
    """Invalid values fail closed with ValueError."""
    with (
        patch.dict(os.environ, {_ENV_NAME: value}, clear=True),
        pytest.raises(ValueError, match=_ENV_NAME),
    ):
        _ = _embed_min_containers_from_env()


def test_embedding_app_wires_min_containers_from_env() -> None:
    """ASGI decorator must use the deploy-import helper (not a hardcoded 1)."""
    source = EMBED_APP.read_text(encoding="utf-8")
    assert "VECINITA_EMBED_MIN_CONTAINERS" in source
    assert "_embed_min_containers_from_env" in source
    assert "min_containers=_EMBED_MIN_CONTAINERS" in source
