"""Regression: eval 502 when generate fails — model not on volume (BUG-2026-07-07).

ADR-037: manifest defaults and staging live on ``vecinita-llm`` (``llm_app``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

_MODEL_ID = "qwen2.5:1.5b-instruct"


def test_read_manifest_defaults_unavailable_when_missing(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Empty volume must not claim default model is downloaded (manifest drift)."""
    from infra.modal import llm_app  # noqa: PLC0415

    path = tmp_path / "manifest.json"
    monkeypatch.setattr(llm_app, "_MANIFEST_PATH", path)
    monkeypatch.setattr(llm_app, "model_volume", MagicMock())

    payload = as_json_object(cast("object", llm_app._list_models_payload()))  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    items_raw = payload.get("items")
    assert isinstance(items_raw, list)
    first = as_json_object(cast("object", items_raw[0]))
    assert first.get("model_id") == _MODEL_ID
    assert first.get("available") is False
