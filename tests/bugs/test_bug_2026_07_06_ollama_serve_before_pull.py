"""Regression: HF model staging for playground pulls (ADR-037; replaces ollama pull)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_download_hf_model_resolves_tag_and_writes_to_volume(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Playground tags download HuggingFace repos under /models/repos/."""
    from infra.modal import llm_app  # noqa: PLC0415

    snapshot = MagicMock()
    fake_hub = ModuleType("huggingface_hub")
    fake_hub.snapshot_download = snapshot  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hub)
    monkeypatch.setattr(llm_app, "_REPOS_ROOT", tmp_path / "repos")

    dest = llm_app._download_hf_model("qwen2.5:3b-instruct")  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    snapshot.assert_called_once_with(
        repo_id="Qwen/Qwen2.5-3B-Instruct",
        local_dir=str(tmp_path / "repos" / "qwen2.5_3b-instruct"),
    )
    assert dest.is_dir()
