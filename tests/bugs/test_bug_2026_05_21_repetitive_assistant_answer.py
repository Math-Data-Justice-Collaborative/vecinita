"""BUG-2026-05-21: Chat answers must not degenerate via unbounded generic LLM loops.

Root cause: Qwen2.5-1.5B with max_tokens=512, no repetition_penalty, and junk retrieval
(e.g. integration fixture "Write API test" at score ~0.01) fed as context.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_APP = REPO_ROOT / "infra" / "modal" / "llm_app.py"
CHAT_CONFIG = REPO_ROOT / "apps" / "chat-rag-backend" / "vecinita_chat_rag_backend" / "config.py"
CHAT_SERVICE = REPO_ROOT / "apps" / "chat-rag-backend" / "vecinita_chat_rag_backend" / "service.py"


def _find_method_body(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    raise AssertionError(f"{class_name}.{method_name} not found")


def _sampling_params_call_has_repetition_penalty(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        func_expr = node.func
        if isinstance(func_expr, ast.Name) and func_expr.id == "SamplingParams":
            for kw in node.keywords:
                if kw.arg == "repetition_penalty":
                    return True
    return False


def test_llm_sampling_params_include_repetition_penalty() -> None:
    """vLLM must penalize token repetition to avoid assistant boilerplate loops."""
    tree = ast.parse(LLM_APP.read_text(encoding="utf-8"))
    generate_text = _find_method_body(tree, "LlmService", "_generate_text")
    assert _sampling_params_call_has_repetition_penalty(generate_text), (
        "SamplingParams in _generate_text must set repetition_penalty"
    )


def test_chat_settings_define_min_retrieval_score() -> None:
    """ChatRAG must expose a minimum pgvector similarity score for chunk inclusion."""
    text = CHAT_CONFIG.read_text(encoding="utf-8")
    assert "min_retrieval_score" in text
    assert "VECINITA_MIN_RETRIEVAL_SCORE" in text


def test_chat_service_wires_score_threshold_to_retriever() -> None:
    """Retrieved junk (e.g. score 0.01) must be filtered before LLM prompt build."""
    text = CHAT_SERVICE.read_text(encoding="utf-8")
    assert "score_threshold" in text
    assert "min_retrieval_score" in text
