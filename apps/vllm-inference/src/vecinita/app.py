"""Main Modal application.

Deployment (persisted app; invoke from outside Modal)
-----------------------------------------------------
    modal deploy src/vecinita/app.py

After deploy, Modal functions can be triggered from Python without HTTP, e.g.
``modal.Function.from_name(app_name, "chat_completion").remote(...)``, which is how
the vecinita gateway can call ``chat_completion`` when ``MODAL_FUNCTION_INVOCATION`` is
set (see Modal docs *Trigger deployed functions* / ``Function.from_name``).

Ephemeral runs (``modal run`` / ``app.run``)
--------------------------------------------
Modal's *Apps, Functions, and entrypoints* guide: use ``with app.run():`` and
``some_function.remote(...)`` from a ``@app.local_entrypoint()`` or
``modal run path::fn``. Here, call a registered function directly, e.g.::

    modal run src/vecinita/app.py::download_model --model-name gemma3

Preloading model weights
------------------------
Run once to pull model weights into the persistent volume; model IDs are in
``config.SUPPORTED_MODELS``. The monorepo ``.github/workflows/modal-deploy.yml``
and this package's ``.github/workflows/deploy.yml`` run ``download_default_model``
after ``modal deploy`` so the default (typically ``gemma3``) is present on the
``vecinita-models`` volume before traffic hits cold containers.

Local HTTP (Docker / Compose)
-----------------------------
For a local Ollama-compatible HTTP stack, use Docker ``vecinita.asgi`` + uvicorn
(see ``Dockerfile``). Do not rely on Modal ``serve`` for this entry file.
"""

from __future__ import annotations

import logging

import modal

from vecinita.config import SUPPORTED_MODELS, resolve_startup_model_id, settings
from vecinita.images import ollama_image
from vecinita.lifecycle import (
    make_default_registry,
    make_lifecycle_event,
    new_correlation_id,
)
from vecinita.models.ollama import classify_connection_error
from vecinita.volumes import MODELS_PATH, models_volume

app = modal.App(settings.app_name)
logger = logging.getLogger(__name__)


def _ensure_vecinita_loggers_visible() -> None:
    """Send INFO logs for ``vecinita.*`` to stderr so Modal captures them.

    The stdlib root logger defaults to WARNING, so ``logger.info`` would be
    invisible in Modal logs while ``print`` still appears; this attaches a
    handler to the package logger so preload/lifecycle messages are visible.
    """
    pkg = logging.getLogger("vecinita")
    pkg.setLevel(logging.INFO)
    if pkg.handlers:
        return
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    pkg.addHandler(handler)
    pkg.propagate = False


_ensure_vecinita_loggers_visible()

# ---------------------------------------------------------------------------
# Weight pre-loading function
# ---------------------------------------------------------------------------


@app.function(
    image=ollama_image,
    volumes={MODELS_PATH: models_volume},
    timeout=3600,  # allow up to 1 h for large models
)
def download_model(model_name: str) -> None:
    """Pull *model_name* into the shared Modal volume.

    This function should be run once (or whenever you add a new model):

        modal run src/vecinita/app.py::download_model --model-name gemma3
    """
    logger.info(
        "download_model entrypoint: pulling configured model into volume "
        "(model_name=%s)",
        model_name,
    )
    if model_name not in SUPPORTED_MODELS:
        supported = ", ".join(SUPPORTED_MODELS)
        raise ValueError(f"Unknown model '{model_name}'. Supported models: {supported}")

    _download_model_if_missing(model_name)


@app.function(
    image=ollama_image,
    volumes={MODELS_PATH: models_volume},
    timeout=3600,
)
def download_default_model() -> None:
    """Ensure the configured default model exists in the shared volume."""
    resolved = resolve_startup_model_id()
    logger.info(
        "download_default_model entrypoint: resolved startup model_id=%s",
        resolved,
    )
    _download_model_if_missing(resolved)


@app.function(
    image=ollama_image,
    volumes={MODELS_PATH: models_volume},
    cpu=4.0,
    scaledown_window=settings.scaledown_window,
    timeout=settings.timeout,
)
def chat_completion(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
) -> dict:
    """Function-style chat completion for non-HTTP Modal invocation."""
    return _chat_completion_impl(
        model=model,
        messages=messages,
        temperature=temperature,
    )  # pragma: no cover


def _resolve_ollama_model_name(model: str | None) -> str:
    """Resolve Ollama model name; blank ``model`` uses ``settings.default_model``.

    Unknown ids fall back to ``settings.default_model`` so callers cannot pass
    fuzzed or arbitrary strings through to ``ollama.Client.chat`` (which may
    respond with HTTP 400 ``model is required``).
    """
    raw = (model or "").strip() or settings.default_model
    meta = SUPPORTED_MODELS.get(raw)
    if meta is not None:
        return str(meta["ollama_name"])
    for entry in SUPPORTED_MODELS.values():
        if entry["ollama_name"] == raw:
            return str(entry["ollama_name"])
    fallback_id = (settings.default_model or "gemma3").strip() or "gemma3"
    logger.warning(
        "chat_completion: unknown model_id=%r; using default_model=%s",
        model,
        fallback_id,
    )
    fallback_meta = SUPPORTED_MODELS.get(fallback_id)
    if fallback_meta is None:
        raise RuntimeError(
            f"default_model {fallback_id!r} is not in SUPPORTED_MODELS; "
            "fix Modal configuration."
        )
    return str(fallback_meta["ollama_name"])


def _chat_completion_impl(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
) -> dict:
    """Chat-completion implementation shared by modal wrapper and unit tests."""
    import subprocess

    import ollama

    ollama_model = _resolve_ollama_model_name(model)

    proc = subprocess.Popen(
        ["ollama", "serve"],
        env=_ollama_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_ollama_ready(timeout_seconds=30)
        _ensure_startup_model_downloaded()
        response = ollama.Client(host=settings.ollama_host).chat(
            model=ollama_model,
            messages=messages,
            options={"temperature": temperature},
        )
        return dict(response)
    finally:
        _run_teardown_lifecycle()
        proc.terminate()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ollama_env() -> dict[str, str]:
    """Return an environment mapping with OLLAMA_MODELS set."""
    import os

    env = os.environ.copy()
    env["OLLAMA_MODELS"] = MODELS_PATH
    return env


def _wait_for_ollama_ready(timeout_seconds: int = 30) -> None:
    """Wait until Ollama responds or raise a clear timeout error."""
    import time

    import ollama

    client = ollama.Client(host=settings.ollama_host)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            client.list()
            return
        except Exception:
            time.sleep(0.5)

    raise RuntimeError(
        f"Ollama server did not become ready within {timeout_seconds} seconds."
    )


def _ensure_startup_model_downloaded() -> None:
    """Ensure configured startup model is cached before serving traffic."""
    _run_startup_lifecycle()


def _ensure_default_model_downloaded() -> None:
    """Backward-compatible helper kept for existing tests/callers."""
    _ensure_startup_model_downloaded()


def _run_startup_lifecycle() -> None:
    correlation_id = new_correlation_id()
    startup_model = resolve_startup_model_id()
    max_attempts = settings.retry_limit
    backoff_seconds = settings.retry_backoff_ms / 1000.0
    if max_attempts < 1:
        raise ValueError(
            "Invalid startup retry configuration: retry_limit must be >= 1 "
            f"(got {max_attempts})."
        )
    retry_window_ms = settings.retry_limit * settings.retry_backoff_ms
    _emit_lifecycle_event(
        make_lifecycle_event(
            event_type="preload_start",
            phase="startup",
            correlation_id=correlation_id,
            details={
                "startup_model": startup_model,
                "retry_limit": settings.retry_limit,
                "retry_backoff_ms": settings.retry_backoff_ms,
                "retry_window_ms": retry_window_ms,
            },
        )
    )
    registry = make_default_registry(
        registry_id=settings.lifecycle_registry_id,
        startup_hook=_startup_preload_hook,
        teardown_hook=_teardown_cache_preserving_hook,
    )
    for attempt in range(1, max_attempts + 1):
        context = {
            "correlation_id": correlation_id,
            "attempt_count": attempt,
            "startup_model": startup_model,
            "failure_phase": "startup",
        }
        try:
            registry.execute_phase("startup", context)
            _emit_lifecycle_event(
                make_lifecycle_event(
                    event_type="preload_success",
                    phase="startup",
                    correlation_id=correlation_id,
                    details={
                        "startup_model": startup_model,
                        "attempt_count": attempt,
                        "retry_window_ms": retry_window_ms,
                    },
                )
            )
            return
        except Exception as exc:
            failure_type = classify_connection_error(exc)
            if failure_type == "permanent_failure":
                _emit_lifecycle_event(
                    make_lifecycle_event(
                        event_type="preload_failure",
                        phase="startup",
                        correlation_id=correlation_id,
                        details=_lifecycle_error_payload(
                            error_code="STARTUP_PRELOAD_PERMANENT_FAILURE",
                            failure_phase="startup",
                            attempt_count=attempt,
                            recommended_operator_action=(
                                "Validate startup model id and registry configuration."
                            ),
                            startup_model=startup_model,
                            retry_window_ms=retry_window_ms,
                            error=str(exc),
                        ),
                    )
                )
                raise RuntimeError(
                    "Startup preload failed with permanent error. "
                    f"startup_model={startup_model}, attempt_count={attempt}"
                ) from exc
            if attempt >= max_attempts:
                _emit_lifecycle_event(
                    make_lifecycle_event(
                        event_type="preload_failure",
                        phase="startup",
                        correlation_id=correlation_id,
                        details=_lifecycle_error_payload(
                            error_code="STARTUP_PRELOAD_FAILED",
                            failure_phase="startup",
                            attempt_count=attempt,
                            recommended_operator_action=(
                                "Verify model id, storage capacity, and source "
                                "availability."
                            ),
                            startup_model=startup_model,
                            retry_window_ms=retry_window_ms,
                            error=str(exc),
                        ),
                    )
                )
                raise RuntimeError(
                    "Startup preload failed after retry limit. "
                    f"startup_model={startup_model}, "
                    f"attempt_count={attempt}, retry_window_ms={retry_window_ms}"
                ) from exc
            _emit_lifecycle_event(
                make_lifecycle_event(
                    event_type="retry",
                    phase="startup",
                    correlation_id=correlation_id,
                    details={
                        "attempt_count": attempt,
                        "next_attempt_in_ms": settings.retry_backoff_ms,
                        "startup_model": startup_model,
                        "error": str(exc),
                    },
                )
            )
            import time

            time.sleep(backoff_seconds)


def _run_teardown_lifecycle(correlation_id: str | None = None) -> None:
    correlation = correlation_id or new_correlation_id()
    registry = make_default_registry(
        registry_id=settings.lifecycle_registry_id,
        startup_hook=_startup_preload_hook,
        teardown_hook=_teardown_cache_preserving_hook,
    )
    _emit_lifecycle_event(
        make_lifecycle_event(
            event_type="teardown_start",
            phase="teardown",
            correlation_id=correlation,
            details={"registry_id": settings.lifecycle_registry_id},
        )
    )
    try:
        registry.execute_phase("teardown", {"correlation_id": correlation})
        _emit_lifecycle_event(
            make_lifecycle_event(
                event_type="teardown_success",
                phase="teardown",
                correlation_id=correlation,
                details={"cache_preserved": True, "temp_artifacts_cleaned": True},
            )
        )
    except Exception as exc:
        _emit_lifecycle_event(
            make_lifecycle_event(
                event_type="teardown_failure",
                phase="teardown",
                correlation_id=correlation,
                details={
                    "error_code": "TEARDOWN_FAILURE",
                    "failure_phase": "teardown",
                    "attempt_count": 1,
                    "recommended_operator_action": (
                        "Inspect teardown logs and verify temp artifact permissions."
                    ),
                    "error": str(exc),
                },
            )
        )
        raise


def _lifecycle_error_payload(
    *,
    error_code: str,
    failure_phase: str,
    attempt_count: int,
    recommended_operator_action: str,
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "error_code": error_code,
        "failure_phase": failure_phase,
        "attempt_count": attempt_count,
        "recommended_operator_action": recommended_operator_action,
    }
    payload.update(extra)
    return payload


def _emit_lifecycle_event(event: dict[str, object]) -> None:
    logger.info("lifecycle_event=%s", event)


def _startup_preload_hook(context: dict[str, object]) -> None:
    model_name = str(context["startup_model"])
    _download_model_if_missing(model_name)


def _teardown_cache_preserving_hook(context: dict[str, object]) -> None:
    # Default teardown intentionally keeps persistent model cache.
    _ = context


def _download_model_if_missing(model_name: str) -> None:
    """Pull *model_name* into the shared volume only when missing."""
    import subprocess

    import ollama

    metadata = SUPPORTED_MODELS.get(model_name)
    if metadata is None:
        raise RuntimeError(
            "Configured startup model "
            f"'{model_name}' is not present in SUPPORTED_MODELS."
        )
    ollama_name = metadata["ollama_name"]

    logger.info(
        "model preload: starting (model_id=%s ollama_name=%s volume=%s)",
        model_name,
        ollama_name,
        MODELS_PATH,
    )

    # Start the Ollama daemon so we can issue pull/list commands through it.
    proc = subprocess.Popen(
        ["ollama", "serve"],
        env=_ollama_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_ollama_ready(timeout_seconds=30)
        logger.info("model preload: ollama server is ready for pull/list")
        client = ollama.Client(host=settings.ollama_host)
        installed = {m.model for m in client.list().models}
        if ollama_name in installed:
            logger.info(
                "model preload: cache hit - '%s' already in volume; skipping pull "
                "(installed_count=%s)",
                ollama_name,
                len(installed),
            )
            return

        logger.info("model preload: pulling %s into models volume ...", ollama_name)
        try:
            client.pull(ollama_name)
        except Exception:
            logger.exception(
                "model preload: pull failed for ollama_name=%s", ollama_name
            )
            raise

        # Persist changes to the volume.
        models_volume.commit()
        logger.info(
            "model preload: success - committed '%s' to models volume at %s",
            ollama_name,
            MODELS_PATH,
        )
    finally:
        proc.terminate()
