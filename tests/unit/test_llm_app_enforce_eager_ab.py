"""S001 T7: A/B toggle for vLLM enforce_eager with GPU memory snapshots."""

from __future__ import annotations

import os
from unittest.mock import patch

from infra.modal.llm_app import _enforce_eager_from_env, _llm_engine_kwargs


def test_enforce_eager_defaults_true_when_env_unset() -> None:
    with patch.dict(os.environ, {}, clear=True):
        assert _enforce_eager_from_env() is True
        assert _llm_engine_kwargs(max_model_len=512)["enforce_eager"] is True


def test_enforce_eager_false_when_env_disabled() -> None:
    for value in ("0", "false", "False", "no", "off"):
        with patch.dict(os.environ, {"VECINITA_LLM_ENFORCE_EAGER": value}, clear=True):
            assert _enforce_eager_from_env() is False
            assert _llm_engine_kwargs(max_model_len=512)["enforce_eager"] is False


def test_enforce_eager_true_when_env_enabled() -> None:
    for value in ("1", "true", "True", "yes", "on"):
        with patch.dict(os.environ, {"VECINITA_LLM_ENFORCE_EAGER": value}, clear=True):
            assert _enforce_eager_from_env() is True
            assert _llm_engine_kwargs(max_model_len=512)["enforce_eager"] is True
