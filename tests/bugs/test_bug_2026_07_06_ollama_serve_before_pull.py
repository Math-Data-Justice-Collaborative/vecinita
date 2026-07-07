"""Regression: pull_model_job must start ollama serve before ollama pull (BUG-2026-07-06)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_run_ollama_pull_starts_serve_before_pull(monkeypatch: MonkeyPatch) -> None:
    """Background pull jobs fail without ollama serve — ensure daemon startup first."""
    from infra.modal import ollama_app  # noqa: PLC0415

    ensure = MagicMock()
    run = MagicMock()
    monkeypatch.setattr(ollama_app, "_ensure_ollama_serve", ensure)
    monkeypatch.setattr(ollama_app.subprocess, "run", run)

    ollama_app._run_ollama_pull("qwen2.5:0.5b-instruct")  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]  # private helper under test

    ensure.assert_called_once_with()
    run.assert_called_once()
