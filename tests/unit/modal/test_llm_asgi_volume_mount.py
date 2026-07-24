"""ASGI list/pull must mount llm-models — otherwise Volume.commit() crash-loops pulls."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LLM_APP = _REPO / "infra" / "modal" / "llm_app.py"
_PLAYGROUND_APP = _REPO / "infra" / "modal" / "llm_playground_app.py"


def _fastapi_function_kwargs(path: Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "fastapi_app":
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            # @app.function(...) or @modal.asgi_app()
            if isinstance(func, ast.Attribute) and func.attr == "function":
                return {kw.arg: kw.value for kw in dec.keywords if kw.arg is not None}
    pytest.fail(f"fastapi_app @app.function(...) not found in {path}")


def test_prod_llm_asgi_attaches_models_volume() -> None:
    """Prod ASGI must mount ``llm-models`` so list/pull can commit the manifest."""
    kwargs = _fastapi_function_kwargs(_LLM_APP)
    assert "volumes" in kwargs, "prod fastapi_app must mount llm-models for manifest commit"


def test_playground_llm_asgi_attaches_models_volume() -> None:
    """Playground ASGI must mount ``llm-models`` so list/pull can commit the manifest."""
    kwargs = _fastapi_function_kwargs(_PLAYGROUND_APP)
    assert "volumes" in kwargs, "playground fastapi_app must mount llm-models for manifest commit"


def test_write_manifest_commits_volume_by_name() -> None:
    """Commit must use Volume.from_name so playground≠prod Volume objects still work."""
    source = _LLM_APP.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_commit_models_volume":
            text = ast.get_source_segment(source, node) or ""
            assert "Volume.from_name" in text or "from_name(VOLUME_NAME" in text, text
            return
    pytest.fail("_commit_models_volume not found")
