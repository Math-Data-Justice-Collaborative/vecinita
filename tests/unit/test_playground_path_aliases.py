"""Path-alias contract for playground model list/pull (RD-166, TP-S010-19, TC-144).

After Ollama→playground rename (T77.5), HTTP paths must remain ``/models/ollama*``
(Modal) and ``/internal/v1/models/ollama*`` (internal-write-api).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LLM_APP = _REPO_ROOT / "infra" / "modal" / "llm_app.py"
_WRITE_APP = _REPO_ROOT / "apps" / "internal-write-api" / "vecinita_internal_write_api" / "app.py"
_LLM_CLIENT = _REPO_ROOT / "packages" / "llm-client" / "vecinita_llm_client" / "client.py"

_MODAL_ALIAS_PATHS = frozenset({"/models/ollama", "/models/ollama/pull"})
_INTERNAL_ALIAS_PATHS = frozenset(
    {
        "/internal/v1/models/ollama",
        "/internal/v1/models/ollama/pull",
        "/internal/v1/models/ollama/catalog",
        "/internal/v1/models/ollama/catalog/{slug}",
    }
)


def _string_constants(tree: ast.AST) -> set[str]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.add(node.value)
    return values


def test_modal_llm_app_keeps_ollama_path_aliases() -> None:
    """Modal ASGI must keep GET/POST ``/models/ollama*`` aliases (RD-166)."""
    tree = ast.parse(_LLM_APP.read_text(encoding="utf-8"))
    constants = _string_constants(tree)
    missing = _MODAL_ALIAS_PATHS - constants
    assert not missing, f"llm_app.py missing path aliases: {sorted(missing)}"


def test_internal_write_api_keeps_ollama_path_aliases() -> None:
    """Internal-write-api must keep ``/internal/v1/models/ollama*`` aliases."""
    tree = ast.parse(_WRITE_APP.read_text(encoding="utf-8"))
    constants = _string_constants(tree)
    missing = _INTERNAL_ALIAS_PATHS - constants
    assert not missing, f"app.py missing path aliases: {sorted(missing)}"


def test_llm_client_requests_ollama_modal_paths() -> None:
    """Unified ``LlmClient`` must call ``/models/ollama`` and ``/models/ollama/pull``."""
    tree = ast.parse(_LLM_CLIENT.read_text(encoding="utf-8"))
    constants = _string_constants(tree)
    assert "/models/ollama" in constants
    assert "/models/ollama/pull" in constants


@pytest.mark.parametrize("path", sorted(_MODAL_ALIAS_PATHS))
def test_modal_alias_path_is_not_playground_prefixed(path: str) -> None:
    """Aliases stay under ``/models/ollama`` — not ``/models/playground`` (TP-S010-19)."""
    assert path.startswith("/models/ollama")
    assert "/playground" not in path
