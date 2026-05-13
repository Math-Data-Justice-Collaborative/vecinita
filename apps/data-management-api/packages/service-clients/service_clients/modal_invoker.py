"""Modal Function.from_name + .remote() helpers for DM service-clients.

Mirrors semantics in ``backend/src/services/modal/invoker.py`` without importing
the monorepo gateway package (submodule boundary).
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from functools import lru_cache
from typing import Any

_logger = logging.getLogger(__name__)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _falsy_explicit_modal_mode(value: str) -> bool:
    return value.strip().lower() in {"0", "false", "no", "off", "http", "rest"}


def _modal_token_pair_configured() -> bool:
    token_id = (os.getenv("MODAL_TOKEN_ID") or os.getenv("MODAL_AUTH_KEY") or "").strip()
    token_secret = (os.getenv("MODAL_TOKEN_SECRET") or os.getenv("MODAL_AUTH_SECRET") or "").strip()
    return bool(token_id and token_secret)


def modal_function_invocation_enabled() -> bool:
    """Whether DM callers should prefer Modal SDK over HTTP to Modal web apps."""
    raw = str(os.getenv("MODAL_FUNCTION_INVOCATION", "")).strip().lower()
    if not raw:
        return False
    if raw == "auto":
        return _modal_token_pair_configured()
    if _falsy_explicit_modal_mode(raw):
        return False
    return _truthy(os.getenv("MODAL_FUNCTION_INVOCATION"))


def modal_environment_name() -> str | None:
    raw = (os.getenv("MODAL_ENVIRONMENT_NAME") or os.getenv("MODAL_ENV") or "").strip()
    return raw or None


def _get_modal_module() -> Any:
    try:
        import modal  # type: ignore[import-not-found]

        return modal
    except Exception as exc:  # pragma: no cover - dev env without modal
        raise RuntimeError(
            "Modal Function invocation requested, but modal SDK is unavailable"
        ) from exc


@lru_cache(maxsize=32)
def _lookup_function(app_name: str, function_name: str, environment_name: str | None) -> Any:
    modal = _get_modal_module()
    if environment_name:
        return modal.Function.from_name(app_name, function_name, environment_name=environment_name)
    return modal.Function.from_name(app_name, function_name)


def clear_modal_function_lookup_cache() -> None:
    """Reset cached Modal function handles (for tests)."""
    _lookup_function.cache_clear()


def lookup_deployed_function(app_name: str, function_name: str) -> Any:
    return _lookup_function(app_name, function_name, modal_environment_name())


def _correlation_id() -> str:
    return (
        (os.getenv("X_REQUEST_ID") or os.getenv("CORRELATION_ID") or os.getenv("VECINITA_TRACE_ID") or "")
        .strip()
        or str(uuid.uuid4())
    )


def _log_modal_call(op: str, *, app_name: str, function_name: str) -> None:
    _logger.info(
        "modal_function_invoke",
        extra={
            "op": op,
            "modal_app": app_name,
            "modal_function": function_name,
            "correlation_id": _correlation_id(),
        },
    )


def scraper_health_modal_sync() -> dict[str, Any]:
    app = (os.getenv("MODAL_SCRAPER_APP_NAME") or "vecinita-scraper").strip()
    fn_name = (os.getenv("MODAL_SCRAPER_HEALTH_FUNCTION") or "health_check").strip()
    _log_modal_call("scraper_health", app_name=app, function_name=fn_name)
    fn = lookup_deployed_function(app, fn_name)
    return fn.remote()


async def scraper_health_modal() -> dict[str, Any]:
    return await asyncio.to_thread(scraper_health_modal_sync)


def embedding_embed_single_modal_sync(text: str, model_version: str | None) -> dict[str, Any]:
    _ = model_version  # Gateway single-text path uses ``embed_query(text)`` only.
    app = (os.getenv("MODAL_EMBEDDING_APP_NAME") or "vecinita-embedding").strip()
    fn_name = (os.getenv("MODAL_EMBEDDING_SINGLE_FUNCTION") or "embed_query").strip()
    _log_modal_call("embedding_embed_query", app_name=app, function_name=fn_name)
    fn = lookup_deployed_function(app, fn_name)
    return fn.remote(text)


async def embedding_embed_single_modal(text: str, model_version: str | None) -> dict[str, Any]:
    return await asyncio.to_thread(embedding_embed_single_modal_sync, text, model_version)


def model_predict_modal_sync(text: str, model_version: str | None) -> dict[str, Any]:
    """Call configured Modal predict/classify function, defaulting to ``predict`` tag."""
    app = (os.getenv("MODAL_MODEL_APP_NAME") or "vecinita-model").strip()
    fn_name = (os.getenv("MODAL_MODEL_PREDICT_FUNCTION") or "predict").strip()
    _log_modal_call("model_predict", app_name=app, function_name=fn_name)
    fn = lookup_deployed_function(app, fn_name)
    if model_version is not None:
        return fn.remote(text=text, model_version=model_version)
    return fn.remote(text=text)


async def model_predict_modal(text: str, model_version: str | None) -> dict[str, Any]:
    return await asyncio.to_thread(model_predict_modal_sync, text, model_version)
