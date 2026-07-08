"""BUG-2026-07-08: golden eval fails with "The read operation timed out".

ADR-037: invariants apply to unified ``vecinita-llm`` (``llm_app.py``). The GPU class and
eval client must allow slow first-token generation for larger sandbox models.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from vecinita_eval.modal_llm import (
    _eval_llm_client,  # pyright: ignore[reportPrivateUsage]  # eval client construction under test
)

if TYPE_CHECKING:
    import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LLM_APP = _REPO_ROOT / "infra" / "modal" / "llm_app.py"

_DEFAULT_CLIENT_TIMEOUT_SECONDS = 120.0


def _parse_llm_app() -> ast.Module:
    return ast.parse(_LLM_APP.read_text(encoding="utf-8"))


def _constant_int(node: ast.expr) -> int | None:
    if not isinstance(node, ast.Constant):
        return None
    raw: object = node.value  # pyright: ignore[reportAny]
    if isinstance(raw, bool):
        return None
    return raw if isinstance(raw, int) else None


def _class_decorator_timeout(tree: ast.Module, class_name: str) -> int | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            for keyword in decorator.keywords:
                if keyword.arg == "timeout":
                    return _constant_int(keyword.value)
    return None


def test_llm_service_class_timeout_covers_slow_generation() -> None:
    """GPU LlmService timeout must exceed interactive client default (900s vs 120s)."""
    tree = _parse_llm_app()
    class_timeout = _class_decorator_timeout(tree, "LlmService")
    assert class_timeout is not None, "LlmService must declare a Modal class timeout"
    assert class_timeout >= 900, (
        f"LlmService timeout ({class_timeout}s) must be >= 900s for golden eval batches"
    )


def test_eval_llm_client_read_timeout_tolerates_slow_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The eval LLM client must use a read timeout above the 120s default (eval-scoped)."""
    captured: dict[str, object] = {}
    real_client = httpx.Client

    def _capture_client(**kwargs: object) -> httpx.Client:
        captured["timeout"] = kwargs.get("timeout")
        return real_client(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "https://example.modal.run")
    monkeypatch.setattr(httpx, "Client", _capture_client)

    client = _eval_llm_client("qwen3:8b")
    assert client is not None, "eval LLM client should be built when VECINITA_MODAL_LLM_URL is set"
    client.close()

    timeout = captured.get("timeout")
    assert isinstance(timeout, (int, float)), "eval LLM client must configure an httpx timeout"
    assert timeout > _DEFAULT_CLIENT_TIMEOUT_SECONDS, (
        "eval LLM client read timeout must exceed 120s for slow first-token generation"
    )
