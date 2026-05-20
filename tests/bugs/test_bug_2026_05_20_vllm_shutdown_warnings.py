"""BUG-2026-05-20: vLLM Modal teardown must destroy NCCL process group."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.modal.llm_app import (  # noqa: E402
    _llm_engine_kwargs,
    _shutdown_vllm_engine,
)


def test_llm_engine_kwargs_use_half_dtype_on_t4() -> None:
    kwargs = _llm_engine_kwargs(max_model_len=512)
    assert kwargs["dtype"] == "half"
    assert kwargs["hf_overrides"]["torch_dtype"] == "float16"


def test_shutdown_vllm_engine_destroys_process_group_when_initialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destroyed: list[bool] = []

    monkeypatch.setattr(
        "infra.modal.llm_app._dist_is_initialized",
        lambda: True,
    )
    monkeypatch.setattr(
        "infra.modal.llm_app._dist_destroy_process_group",
        lambda: destroyed.append(True),
    )

    mock_llm = MagicMock()
    mock_llm.llm_engine = None

    _shutdown_vllm_engine(mock_llm)

    assert destroyed == [True]


def test_shutdown_vllm_engine_skips_destroy_when_not_initialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destroyed: list[bool] = []

    monkeypatch.setattr(
        "infra.modal.llm_app._dist_is_initialized",
        lambda: False,
    )
    monkeypatch.setattr(
        "infra.modal.llm_app._dist_destroy_process_group",
        lambda: destroyed.append(True),
    )

    _shutdown_vllm_engine(None)

    assert destroyed == []
