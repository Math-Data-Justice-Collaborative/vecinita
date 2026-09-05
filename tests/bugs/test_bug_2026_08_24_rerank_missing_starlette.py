"""BUG-2026-08-24: vecinita-rerank ASGI crash — starlette missing from Modal image."""

from __future__ import annotations

from pathlib import Path


def test_rerank_modal_image_includes_starlette() -> None:
    """rerank_api ASGI requires starlette in pip_install (F45 / EV-029 / AC-SR7)."""
    source = Path("infra/modal/rerank_app.py").read_text(encoding="utf-8")
    assert "starlette" in source, "rerank_app.py must pip_install starlette for rerank_api ASGI"
