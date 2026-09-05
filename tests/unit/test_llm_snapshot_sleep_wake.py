"""PR review advisories: fail-closed Level-1 sleep/wake on snapshot path (EV-313).

[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-313]
[Spec: docs/test-plan.md §TC-313-01]
"""

# ruff: noqa: SLF001

from __future__ import annotations

import sys
import types
from typing import ClassVar, Literal
from unittest.mock import MagicMock, patch

import pytest
from infra.modal.llm_service_core import LlmServiceCore


class _ProdCore(LlmServiceCore):
    """Minimal prod-shaped core for unit tests (no Modal decorators)."""

    serve_role: ClassVar[Literal["prod", "playground"]] = "prod"
    allow_model_reload: ClassVar[bool] = False


def _install_fake_vllm(*, llm: object) -> None:
    """Register a stub ``vllm`` module so snapshot helpers can import LLM."""
    fake = types.ModuleType("vllm")
    fake.LLM = MagicMock(return_value=llm)  # type: ignore[attr-defined]
    fake.SamplingParams = MagicMock()  # type: ignore[attr-defined]
    sys.modules["vllm"] = fake


class _LlmNoSleep:
    """vLLM stand-in without ``sleep``."""

    def generate(self, prompts: list[str], params: object) -> list[object]:
        _ = (prompts, params)
        return []


class _LlmWithSleep:
    """vLLM stand-in with Level-1 ``sleep``."""

    def __init__(self) -> None:
        self.sleep_calls: list[int] = []

    def generate(self, prompts: list[str], params: object) -> list[object]:
        _ = (prompts, params)
        return []

    def sleep(self, level: int = 1) -> None:
        self.sleep_calls.append(level)


class _LlmNoWake:
    """Engine present but missing ``wake_up``."""


class _LlmWithWake:
    """Engine with ``wake_up`` for restore happy path."""

    def __init__(self) -> None:
        self.wake_calls = 0

    def wake_up(self) -> None:
        self.wake_calls += 1


def test_snapshot_enter_build_raises_when_sleep_missing() -> None:
    """Snapshot build must fail closed if vLLM has no Level-1 sleep."""
    core = _ProdCore()
    _install_fake_vllm(llm=_LlmNoSleep())
    try:
        with (
            patch("infra.modal.llm_app._llm_engine_kwargs", return_value={"model": "m"}),
            patch("infra.modal.llm_app.max_model_len_for", return_value=512),
            patch("infra.modal.llm_app.MODEL_ID", "m"),
            pytest.raises(TypeError, match="Level-1 sleep"),
        ):
            core._snapshot_enter_build()  # pyright: ignore[reportPrivateUsage]
    finally:
        _ = sys.modules.pop("vllm", None)


def test_snapshot_enter_build_calls_sleep_level_one_when_present() -> None:
    """Happy path: sleep(level=1) then mark snapshot mode."""
    core = _ProdCore()
    llm = _LlmWithSleep()
    _install_fake_vllm(llm=llm)
    try:
        with (
            patch("infra.modal.llm_app._llm_engine_kwargs", return_value={"model": "m"}),
            patch("infra.modal.llm_app.max_model_len_for", return_value=512),
            patch("infra.modal.llm_app.MODEL_ID", "m"),
        ):
            core._snapshot_enter_build()  # pyright: ignore[reportPrivateUsage]
    finally:
        _ = sys.modules.pop("vllm", None)

    assert llm.sleep_calls == [1]
    assert core._snapshot_mode is True  # pyright: ignore[reportPrivateUsage]


def test_snapshot_enter_restore_raises_when_wake_up_missing() -> None:
    """Snapshot restore must fail closed if wake_up is absent."""
    core = _ProdCore()
    core._llm = _LlmNoWake()  # pyright: ignore[reportPrivateUsage]

    with pytest.raises(TypeError, match="wake_up"):
        core._snapshot_enter_restore()  # pyright: ignore[reportPrivateUsage]


def test_snapshot_enter_restore_wakes_then_binds_lora() -> None:
    """Happy path: wake_up then LoRA bind."""
    core = _ProdCore()
    llm = _LlmWithWake()
    core._llm = llm  # pyright: ignore[reportPrivateUsage]
    bind_calls = {"n": 0}

    def _bind() -> None:
        bind_calls["n"] += 1

    with patch.object(core, "_bind_lora_after_restore", side_effect=_bind):
        core._snapshot_enter_restore()  # pyright: ignore[reportPrivateUsage]

    assert llm.wake_calls == 1
    assert bind_calls["n"] == 1
    assert core._snapshot_mode is True  # pyright: ignore[reportPrivateUsage]
