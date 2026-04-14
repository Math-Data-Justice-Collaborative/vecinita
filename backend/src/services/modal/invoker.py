"""Modal Function invocation helpers for gateway / agent paths.

These helpers provide a non-HTTP integration mode so callers can invoke Modal
workloads via ``modal.Function.from_name(...).remote(...)`` (Modal SDK 1.x)
instead of hitting ``*.modal.run`` web endpoints.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def modal_function_invocation_enabled() -> bool:
    """Return whether backend should prefer Modal Function invocation."""
    return _truthy(os.getenv("MODAL_FUNCTION_INVOCATION", "false"))


def _modal_environment_name() -> str | None:
    """Optional Modal deployment environment (staging/production), if set."""
    raw = (os.getenv("MODAL_ENVIRONMENT_NAME") or os.getenv("MODAL_ENV") or "").strip()
    return raw or None


def _get_modal_module():
    try:
        import modal  # type: ignore[import-not-found]

        return modal
    except Exception as exc:  # pragma: no cover - exercised in environments without modal
        raise RuntimeError(
            "Modal Function invocation requested, but modal SDK is unavailable"
        ) from exc


@lru_cache(maxsize=32)
def _lookup_function(app_name: str, function_name: str, environment_name: str | None):
    """Resolve a deployed Modal function by app name and function name.

    Uses :meth:`modal.Function.from_name` (Modal 1.x). Legacy ``Function.lookup``
    is not available in current SDKs.
    """
    modal = _get_modal_module()
    if environment_name:
        return modal.Function.from_name(app_name, function_name, environment_name=environment_name)
    return modal.Function.from_name(app_name, function_name)


def _invoke_env() -> str | None:
    return _modal_environment_name()


def invoke_modal_embedding_single(text: str) -> dict[str, Any]:
    app_name = os.getenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
    fn_name = os.getenv("MODAL_EMBEDDING_SINGLE_FUNCTION", "embed_query")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(text)


def invoke_modal_embedding_batch(texts: list[str]) -> dict[str, Any]:
    app_name = os.getenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
    fn_name = os.getenv("MODAL_EMBEDDING_BATCH_FUNCTION", "embed_batch")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(texts)


def invoke_modal_scraper_reindex(clean: bool, stream: bool, verbose: bool) -> dict[str, Any]:
    app_name = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
    fn_name = os.getenv("MODAL_SCRAPER_REINDEX_FUNCTION", "trigger_reindex")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(clean=clean, stream=stream, verbose=verbose)


def invoke_modal_model_chat(
    model: str, messages: list[dict[str, str]], temperature: float
) -> dict[str, Any]:
    app_name = os.getenv("MODAL_MODEL_APP_NAME", "vecinita-model")
    fn_name = os.getenv("MODAL_MODEL_CHAT_FUNCTION", "chat_completion")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(model=model, messages=messages, temperature=temperature)
