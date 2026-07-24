"""TC-141 / RD-168 / TP-S010-26: catalog/list/pull gated by resolve_hf_repo."""

from __future__ import annotations

import ast
import sys
from http import HTTPStatus
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_shared_schemas.playground_catalog import PLAYGROUND_MODEL_CATALOG
from vecinita_shared_schemas.playground_hf_registry import resolve_hf_repo

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.modal import llm_app  # noqa: E402
from infra.modal.llm_app import (  # noqa: E402
    DEFAULT_PLAYGROUND_MODEL_ID,
    _list_models_payload,  # pyright: ignore[reportPrivateUsage]  # catalog gate under test
    _write_manifest,  # pyright: ignore[reportPrivateUsage]  # catalog gate under test
)

LLM_APP = _REPO_ROOT / "infra" / "modal" / "llm_app.py"
_UNMAPPED_TAG = "unknown-custom:7b"


def _find_fastapi_handler(name: str) -> ast.AsyncFunctionDef:
    tree = ast.parse(LLM_APP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    msg = f"async handler {name} not found in llm_app.py"
    raise AssertionError(msg)


def _handler_source(name: str) -> str:
    """Return the source text of a nested ASGI handler (line-accurate)."""
    tree = ast.parse(LLM_APP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            lines = LLM_APP.read_text(encoding="utf-8").splitlines()
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    msg = f"async handler {name} not found in llm_app.py"
    raise AssertionError(msg)


@pytest.fixture
def manifest_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect manifest I/O to a temp directory."""
    path = tmp_path / "manifest.json"
    monkeypatch.setattr(llm_app, "_MANIFEST_PATH", path)
    monkeypatch.setattr(llm_app, "model_volume", MagicMock())
    monkeypatch.setattr(llm_app, "_commit_models_volume", MagicMock())
    return path


def test_playground_catalog_tags_all_resolve_hf_repo() -> None:
    """Curated catalog ⊆ resolve_hf_repo (TC-141 / RD-168)."""
    for model_id in PLAYGROUND_MODEL_CATALOG:
        repo = resolve_hf_repo(model_id)
        assert isinstance(repo, str)
        assert "/" in repo


def test_pull_model_gates_unmapped_tag_with_bad_request() -> None:
    """Unmapped pull must return HTTP 400 before spawn (TP-S010-26 / TC-141)."""
    source = _handler_source("pull_model")
    assert "resolve_hf_repo" in source, (
        "pull_model must call resolve_hf_repo before spawning pull_model_job (RD-168 / TP-S010-26)"
    )
    assert "BAD_REQUEST" in source or str(HTTPStatus.BAD_REQUEST) in source, (
        "pull_model must return HTTP 400 (BAD_REQUEST) when model_id is unmapped "
        "(TC-141 / TP-S010-26)"
    )
    # Must not spawn until mapping succeeds.
    spawn_idx = source.find("pull_model_job.spawn")
    resolve_idx = source.find("resolve_hf_repo")
    assert spawn_idx >= 0, "pull_model must still spawn pull_model_job for mapped tags"
    assert 0 <= resolve_idx < spawn_idx, (
        "resolve_hf_repo must run before pull_model_job.spawn so unmapped tags never enqueue"
    )


def test_list_models_payload_excludes_unmapped_manifest_tags(
    manifest_path: Path,
) -> None:
    """List payload must omit tags resolve_hf_repo rejects (TC-141)."""
    _ = manifest_path
    _write_manifest(
        [
            {"model_id": DEFAULT_PLAYGROUND_MODEL_ID, "available": True},
            {"model_id": _UNMAPPED_TAG, "available": True},
        ]
    )
    payload = as_json_object(cast("object", _list_models_payload()))
    items_raw = payload.get("items")
    assert isinstance(items_raw, list)
    model_ids = [as_json_object(raw).get("model_id") for raw in cast("list[object]", items_raw)]
    assert DEFAULT_PLAYGROUND_MODEL_ID in model_ids
    assert _UNMAPPED_TAG not in model_ids, (
        "list_models must filter tags that resolve_hf_repo rejects (RD-168 / TP-S010-26 / TC-141)"
    )


def test_pull_model_handler_exists_for_gate() -> None:
    """Sanity: pull_model ASGI handler is present (gate target for T79.5)."""
    handler = _find_fastapi_handler("pull_model")
    assert handler.name == "pull_model"
