"""BUG-2026-05-21: stream_tokens must not call self.complete() (Modal Function wrapper).

Direct self.complete(...) inside @modal.method raises:
  TypeError: 'Function' object is not callable
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_APP = REPO_ROOT / "infra" / "modal" / "llm_app.py"


def _find_stream_tokens_body(tree: ast.AST) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "LlmService":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "stream_tokens":
                    return item
    msg = "LlmService.stream_tokens not found in llm_app.py"
    raise AssertionError(msg)


def _calls_self_complete(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        func_expr = node.func
        if (
            isinstance(func_expr, ast.Attribute)
            and isinstance(func_expr.value, ast.Name)
            and func_expr.value.id == "self"
            and func_expr.attr == "complete"
        ):
            return True
    return False


def test_stream_tokens_does_not_call_self_complete_directly() -> None:
    """Regression: use shared generate helper, not Modal-wrapped self.complete()."""
    tree = ast.parse(LLM_APP.read_text(encoding="utf-8"))
    stream_tokens = _find_stream_tokens_body(tree)
    assert not _calls_self_complete(stream_tokens), (
        "stream_tokens must not call self.complete(...); use _generate_text or .local()"
    )
