"""TC-142 / UJ-049 / RD-165: proxy key required on generate/warm/models; health open."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.modal.llm_app import (  # noqa: E402
    _PROXY_ENV,
    _PROXY_HEADER,
    _authorized,  # pyright: ignore[reportPrivateUsage]  # auth helper under test
)

LLM_APP = _REPO_ROOT / "infra" / "modal" / "llm_app.py"


def _find_fastapi_handler(name: str) -> ast.AsyncFunctionDef:
    tree = ast.parse(LLM_APP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    msg = f"async handler {name} not found in llm_app.py"
    raise AssertionError(msg)


def _calls_authorized(func: ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        func_expr = node.func
        if isinstance(func_expr, ast.Name) and func_expr.id == "_authorized":
            return True
    return False


def test_authorized_rejects_when_proxy_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail closed when VECINITA_MODAL_PROXY_KEY is unset (RD-165)."""
    monkeypatch.delenv(_PROXY_ENV, raising=False)
    request = MagicMock()
    request.headers.get.return_value = "any-key"
    assert _authorized(request) is False


def test_authorized_rejects_wrong_proxy_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wrong X-Vecinita-Proxy-Key is unauthorized."""
    monkeypatch.setenv(_PROXY_ENV, "expected-secret")
    request = MagicMock()
    request.headers.get.return_value = "wrong-secret"
    assert _authorized(request) is False
    request.headers.get.assert_called_with(_PROXY_HEADER)


def test_authorized_accepts_matching_proxy_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Matching proxy key header authorizes the request."""
    monkeypatch.setenv(_PROXY_ENV, "expected-secret")
    request = MagicMock()
    request.headers.get.return_value = "expected-secret"
    assert _authorized(request) is True


@pytest.mark.parametrize(
    "handler_name",
    ("generate", "generate_stream", "warm", "list_models", "pull_model"),
)
def test_asgi_handler_requires_authorized(handler_name: str) -> None:
    """TC-142: all non-health LLM routes must call _authorized (UJ-049)."""
    handler = _find_fastapi_handler(handler_name)
    assert _calls_authorized(handler), (
        f"{handler_name} must call _authorized(...) and return 401 when unauthorized "
        "(RD-165 / TP-S010-23 / TC-142)"
    )


def test_health_handler_does_not_require_authorized() -> None:
    """TC-142: /health may stay open without proxy key."""
    handler = _find_fastapi_handler("health")
    assert not _calls_authorized(handler)
