"""Modal Function invocation helpers for gateway / agent paths.

Deployed apps (after ``modal deploy``): use ``modal.Function.from_name(...)`` +
``.remote()`` / ``.spawn()`` from any Python client with Modal auth — the pattern
described in Modal's "Apps, Functions, and entrypoints" and "Trigger deployed functions"
guides (https://modal.com/docs/guide/apps,
https://modal.com/docs/guide/trigger-deployed-functions).

Ephemeral apps (``modal run`` / ``with app.run():``): call ``.remote()`` on the
function handle attached to your local ``modal.App`` (e.g. inside an
``@app.local_entrypoint()``); that is for dev / one-off jobs, not this gateway module.

See https://modal.com/docs/reference/modal.Function — ``spawn`` returns a
``FunctionCall``; we use ``.get(timeout=...)`` when the gateway still needs a
result payload (e.g. reindex trigger acknowledgement).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _falsy_explicit_modal_mode(value: str) -> bool:
    return value.strip().lower() in {"0", "false", "no", "off", "http", "rest"}


def _modal_token_pair_configured() -> bool:
    """True when Modal SDK can authenticate (canonical or legacy env names)."""
    token_id = (os.getenv("MODAL_TOKEN_ID") or os.getenv("MODAL_TOKEN_ID") or "").strip()
    token_secret = (
        os.getenv("MODAL_TOKEN_SECRET") or os.getenv("MODAL_TOKEN_SECRET") or ""
    ).strip()
    return bool(token_id and token_secret)


def modal_function_invocation_enabled() -> bool:
    """Return whether backend should prefer Modal Function invocation over HTTP.

    * Unset or empty — **disabled** (use HTTP / gateway defaults). Keeps local tests
      and mixed env files predictable when Modal tokens are present for other tools.
    * ``auto`` — enable only when a Modal token pair is configured (see
      ``_modal_token_pair_configured``); otherwise HTTP.
    * ``true``, ``1``, ``yes``, ``on`` — always enable (Modal SDK + auth required).
    * ``false``, ``http``, ``rest``, … — force HTTP even if tokens exist.
    """
    raw = str(os.getenv("MODAL_FUNCTION_INVOCATION", "")).strip().lower()
    if not raw:
        return False
    if raw == "auto":
        return _modal_token_pair_configured()
    if _falsy_explicit_modal_mode(raw):
        return False
    return _truthy(os.getenv("MODAL_FUNCTION_INVOCATION"))


def modal_function_invocation_mode() -> str:
    """Return normalized invocation mode: ``off`` | ``auto`` | ``on``."""
    raw = str(os.getenv("MODAL_FUNCTION_INVOCATION", "")).strip().lower()
    if not raw or _falsy_explicit_modal_mode(raw):
        return "off"
    if raw == "auto":
        return "auto"
    return "on"


def modal_token_pair_configured() -> bool:
    """Expose whether a Modal token pair is configured."""
    return _modal_token_pair_configured()


def enforce_modal_function_policy_for_urls(urls: dict[str, str | None]) -> None:
    """Fail fast when ``*.modal.run`` URLs are configured without function invocation."""
    modal_targets = [
        (name, str(value).strip())
        for name, value in urls.items()
        if value and "modal.run" in str(value).strip().lower()
    ]
    if not modal_targets:
        return

    if not modal_function_invocation_enabled():
        targets = ", ".join(f"{name}={value}" for name, value in modal_targets)
        raise RuntimeError(
            "Configured Modal HTTP endpoints require Modal function invocation. "
            f"Set MODAL_FUNCTION_INVOCATION=auto or 1 and provide MODAL_TOKEN_ID/MODAL_TOKEN_SECRET. "
            f"Targets: {targets}"
        )

    if not _modal_token_pair_configured():
        targets = ", ".join(name for name, _ in modal_targets)
        raise RuntimeError(
            "Modal function invocation is enabled for Modal-hosted targets but Modal tokens are missing. "
            "Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET (or MODAL_TOKEN_ID/MODAL_TOKEN_SECRET). "
            f"Targets: {targets}"
        )


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
    timeout_raw = os.getenv("MODAL_SCRAPER_REINDEX_FUNCTION_TIMEOUT", "120").strip()
    try:
        timeout_s = float(timeout_raw)
    except ValueError:
        timeout_s = 120.0
    call = fn.spawn(clean=clean, stream=stream, verbose=verbose)
    return call.get(timeout=timeout_s)


def invoke_modal_model_chat(
    model: str, messages: list[dict[str, str]], temperature: float
) -> dict[str, Any]:
    app_name = os.getenv("MODAL_MODEL_APP_NAME", "vecinita-model")
    fn_name = os.getenv("MODAL_MODEL_CHAT_FUNCTION", "chat_completion")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(model=model, messages=messages, temperature=temperature)


def spawn_modal_scraper_reindex(clean: bool, stream: bool, verbose: bool) -> Any:
    """Spawn ``trigger_reindex`` (or configured function) without blocking on the result."""
    app_name = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
    fn_name = os.getenv("MODAL_SCRAPER_REINDEX_FUNCTION", "trigger_reindex")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.spawn(clean=clean, stream=stream, verbose=verbose)


def get_modal_function_call_result(function_call_id: str, timeout: float | None) -> Any:
    """Resolve a ``FunctionCall`` by id and ``get`` its result (may raise ``TimeoutError``)."""
    modal = _get_modal_module()
    fc = modal.FunctionCall.from_id(function_call_id)
    return fc.get(timeout=timeout)


def invoke_modal_scrape_job_submit(payload: dict[str, Any]) -> dict[str, Any]:
    """Call scraper ``modal_scrape_job_submit``; returns Modal RPC envelope dict."""
    app_name = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
    fn_name = os.getenv("MODAL_SCRAPER_JOB_SUBMIT_FUNCTION", "modal_scrape_job_submit")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(payload)


def invoke_modal_scrape_job_get(job_id: str) -> dict[str, Any]:
    app_name = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
    fn_name = os.getenv("MODAL_SCRAPER_JOB_GET_FUNCTION", "modal_scrape_job_get")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(job_id)


def invoke_modal_scrape_job_list(user_id: str | None, limit: int) -> dict[str, Any]:
    app_name = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
    fn_name = os.getenv("MODAL_SCRAPER_JOB_LIST_FUNCTION", "modal_scrape_job_list")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(user_id=user_id, limit=limit)


def invoke_modal_scrape_job_cancel(job_id: str) -> dict[str, Any]:
    app_name = os.getenv("MODAL_SCRAPER_APP_NAME", "vecinita-scraper")
    fn_name = os.getenv("MODAL_SCRAPER_JOB_CANCEL_FUNCTION", "modal_scrape_job_cancel")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(job_id)
