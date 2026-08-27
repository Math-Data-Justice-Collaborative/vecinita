"""TC-143 / RD-164: stream_tokens must emit real incremental tokens (not full-then-split)."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LLM_APP = REPO_ROOT / "infra" / "modal" / "llm_app.py"


def _find_llm_service_method(name: str) -> ast.FunctionDef:
    tree = ast.parse(LLM_APP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "LlmService":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    return item
    msg = f"LlmService.{name} not found in llm_app.py"
    raise AssertionError(msg)


def _calls_attr(func: ast.FunctionDef, *, attr: str) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        func_expr = node.func
        if isinstance(func_expr, ast.Attribute) and func_expr.attr == attr:
            return True
    return False


def _calls_self_method(func: ast.FunctionDef, *, method: str) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        func_expr = node.func
        if (
            isinstance(func_expr, ast.Attribute)
            and isinstance(func_expr.value, ast.Name)
            and func_expr.value.id == "self"
            and func_expr.attr == method
        ):
            return True
    return False


def test_stream_tokens_does_not_word_chunk_full_completion() -> None:
    """Regression guard: no text.split() after a completed reply (fake SSE)."""
    stream_tokens = _find_llm_service_method("stream_tokens")
    assert not _calls_attr(stream_tokens, attr="split"), (
        "stream_tokens must not word-chunk a full completion via .split(); "
        + "wire vLLM incremental token streaming (RD-164 / TP-S010-22 / TC-143)"
    )


def test_stream_tokens_does_not_call_generate_text_for_full_reply() -> None:
    """Real streaming must not wait on _generate_text then re-slice the reply."""
    stream_tokens = _find_llm_service_method("stream_tokens")
    assert not _calls_self_method(stream_tokens, method="_generate_text"), (
        "stream_tokens must not call self._generate_text(...) then yield pieces; "
        + "use vLLM engine streaming / async iterator (TP-S010-22)"
    )
