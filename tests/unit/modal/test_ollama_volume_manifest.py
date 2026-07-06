"""TC-139: Modal vecinita-models manifest read/write contract (F38 / EV-010)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from vecinita_shared_schemas.json_types import as_json_object

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.modal import ollama_app  # noqa: E402
from infra.modal.ollama_app import (  # noqa: E402
    DEFAULT_MODEL_ID,
    _list_models_payload,  # pyright: ignore[reportPrivateUsage]  # manifest contract under test
    _write_manifest,  # pyright: ignore[reportPrivateUsage]  # manifest contract under test
)


@pytest.fixture
def manifest_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect manifest I/O to a temp directory."""
    path = tmp_path / "manifest.json"
    monkeypatch.setenv("MODAL_ENVIRONMENT", "test")
    monkeypatch.setattr(ollama_app, "_MANIFEST_PATH", path)
    monkeypatch.setattr(ollama_app, "model_volume", MagicMock())
    return path


def test_read_manifest_defaults_when_missing(manifest_path: Path) -> None:
    """Empty volume returns the default playground model entry."""
    _ = manifest_path
    payload = as_json_object(cast("object", _list_models_payload()))
    items_raw = payload.get("items")
    assert isinstance(items_raw, list)
    first = as_json_object(cast("object", items_raw[0]))
    assert first.get("model_id") == DEFAULT_MODEL_ID
    assert first.get("available") is True


def test_write_manifest_marks_model_unavailable_then_available(
    manifest_path: Path,
) -> None:
    """Manifest updates propagate to list payload (Modal volume contract)."""
    model_id = "qwen2.5:3b-instruct"

    _write_manifest(
        [
            {"model_id": DEFAULT_MODEL_ID, "available": True},
            {"model_id": model_id, "available": False},
        ]
    )
    pulling = as_json_object(cast("object", _list_models_payload()))
    pulling_items = pulling.get("items")
    assert isinstance(pulling_items, list)
    pulling_entry: object | None = None
    for raw_item in cast("list[object]", pulling_items):
        item = as_json_object(raw_item)
        if item.get("model_id") == model_id:
            pulling_entry = item
            break
    assert pulling_entry is not None
    assert as_json_object(cast("object", pulling_entry)).get("available") is False

    _write_manifest(
        [
            {"model_id": DEFAULT_MODEL_ID, "available": True},
            {"model_id": model_id, "available": True},
        ]
    )
    ready = as_json_object(cast("object", _list_models_payload()))
    ready_items = ready.get("items")
    assert isinstance(ready_items, list)
    ready_entry: object | None = None
    for raw_item in cast("list[object]", ready_items):
        item = as_json_object(raw_item)
        if item.get("model_id") == model_id:
            ready_entry = item
            break
    assert ready_entry is not None
    assert as_json_object(cast("object", ready_entry)).get("available") is True
    assert manifest_path.exists()
    stored_obj = as_json_object(
        cast("object", json.loads(manifest_path.read_text(encoding="utf-8")))
    )
    models_raw = stored_obj.get("models")
    assert isinstance(models_raw, list)
