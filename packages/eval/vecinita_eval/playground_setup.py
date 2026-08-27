"""Playground LLM model list / ensure-ready helpers for golden-set eval setup.

Uses ``VECINITA_MODAL_LLM_PLAYGROUND_URL`` (ADR-037 / TP-S010-27) with path aliases
``/models/ollama`` and ``/models/ollama/pull`` via ``LlmClient``.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from vecinita_llm_client import LlmClient, LlmClientError

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_shared_schemas.playground_models import PlaygroundModelListResponse

_ENV_PLAYGROUND: Final[str] = "VECINITA_MODAL_LLM_PLAYGROUND_URL"
_ENV_LLM: Final[str] = "VECINITA_MODAL_LLM_URL"
_ENV_OLLAMA: Final[str] = "VECINITA_MODAL_OLLAMA_URL"

DEFAULT_POLL_INTERVAL_S: Final[float] = 5.0
DEFAULT_PULL_TIMEOUT_S: Final[float] = 900.0
DEFAULT_CLIENT_TIMEOUT_S: Final[float] = 120.0


class PlaygroundSetupError(RuntimeError):
    """Playground list/pull/warm setup could not complete."""


@dataclass(frozen=True, slots=True)
class ModelReadyResult:
    """Outcome of ensuring a playground model is staged and optionally warmed."""

    model_id: str
    was_available: bool
    pulled: bool
    job_id: str | None
    warmed: bool
    available: bool


def assert_no_legacy_ollama_url() -> None:
    """Raise if deprecated ``VECINITA_MODAL_OLLAMA_URL`` is set.

    Raises:
    ------
    PlaygroundSetupError
        When the legacy Ollama URL env var is present (ADR-037).
    """
    if os.environ.get(_ENV_OLLAMA, "").strip():
        msg = f"{_ENV_OLLAMA} must be unset (ADR-037); use {_ENV_PLAYGROUND} for list/pull"
        raise PlaygroundSetupError(msg)


def resolve_playground_base_url(*, base_url: str | None = None) -> str:
    """Resolve the Modal playground (or fallback LLM) base URL for list/pull/warm.

    Parameters
    ----------
    base_url : str or None
        Explicit override. When omitted, prefers ``VECINITA_MODAL_LLM_PLAYGROUND_URL``,
        then falls back to ``VECINITA_MODAL_LLM_URL``.

    Returns:
    -------
    str
        Base URL without a trailing slash.

    Raises:
    ------
    PlaygroundSetupError
        When no URL can be resolved.
    """
    assert_no_legacy_ollama_url()
    resolved = (
        (base_url or "").strip()
        or os.environ.get(_ENV_PLAYGROUND, "").strip()
        or os.environ.get(_ENV_LLM, "").strip()
    )
    if not resolved:
        msg = (
            f"{_ENV_PLAYGROUND} (preferred) or {_ENV_LLM} or --base-url is required "
            + "for playground model list/setup"
        )
        raise PlaygroundSetupError(msg)
    return resolved.rstrip("/")


def make_playground_client(
    *,
    base_url: str | None = None,
    model_id: str | None = None,
    timeout: float = DEFAULT_CLIENT_TIMEOUT_S,
    require_proxy_key: bool = True,
) -> LlmClient:
    """Build an ``LlmClient`` pointed at the playground (or fallback) LLM app.

    Parameters
    ----------
    base_url : str or None
        Explicit Modal ASGI base URL.
    model_id : str or None
        Default model tag for ``/warm`` and generate.
    timeout : float
        HTTP timeout in seconds.
    require_proxy_key : bool
        When True, require ``VECINITA_MODAL_PROXY_KEY`` (list/pull/warm auth).

    Returns:
    -------
    LlmClient
        Configured HTTP client.
    """
    return LlmClient(
        resolve_playground_base_url(base_url=base_url),
        model_id=model_id,
        timeout=timeout,
        require_proxy_key=require_proxy_key,
    )


def model_is_available(listing: PlaygroundModelListResponse, model_id: str) -> bool:
    """Return whether ``model_id`` is present and ``available`` in a listing.

    Parameters
    ----------
    listing : PlaygroundModelListResponse
        Response from ``GET /models/ollama``.
    model_id : str
        Playground model tag.

    Returns:
    -------
    bool
        True when the tag is listed and marked available.
    """
    needle = model_id.strip()
    return any(item.model_id == needle and item.available for item in listing.items)


def format_model_listing(listing: PlaygroundModelListResponse) -> str:
    r"""Format a model listing as sorted ``model_id\tavailable=...`` lines.

    Parameters
    ----------
    listing : PlaygroundModelListResponse
        Models staged on the ``llm-models`` volume.

    Returns:
    -------
    str
        Human-readable multi-line listing (empty string when no items).
    """
    lines = [
        f"{item.model_id}\tavailable={'true' if item.available else 'false'}"
        for item in sorted(listing.items, key=lambda row: row.model_id)
    ]
    return "\n".join(lines)


def _list_or_raise(client: LlmClient, *, context: str) -> PlaygroundModelListResponse:
    try:
        return client.list_models()
    except LlmClientError as exc:
        msg = f"list_models failed{context}: {exc}"
        raise PlaygroundSetupError(msg) from exc


def _pull_if_needed(  # noqa: PLR0913  # pull/wait/poll knobs mirrored from ensure_model_ready
    client: LlmClient,
    tag: str,
    *,
    pull_if_missing: bool,
    wait: bool,
    poll_interval_s: float,
    timeout_s: float,
    sleep: Callable[[float], None],
) -> tuple[bool, bool, str | None]:
    """Return ``(was_available, pulled, job_id)`` after optional pull/wait."""
    listing = _list_or_raise(client, context="")
    was_available = model_is_available(listing, tag)
    if was_available:
        return True, False, None
    if not pull_if_missing:
        msg = f"model {tag!r} is not available on the playground volume"
        raise PlaygroundSetupError(msg)
    try:
        pull = client.start_pull(tag)
    except LlmClientError as exc:
        msg = f"start_pull failed for {tag!r}: {exc}"
        raise PlaygroundSetupError(msg) from exc
    if wait:
        _wait_until_available(
            client,
            tag,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            sleep=sleep,
        )
    return False, True, str(pull.job_id)


def _warm_if_requested(client: LlmClient, tag: str, *, available: bool, warm: bool) -> bool:
    if not warm:
        return False
    if not available:
        msg = f"cannot warm {tag!r}: model is not available yet (use --wait)"
        raise PlaygroundSetupError(msg)
    if client.default_model_id != tag:
        msg = (
            f"client default_model_id {client.default_model_id!r} != {tag!r}; "
            + "construct LlmClient/make_playground_client with model_id set"
        )
        raise PlaygroundSetupError(msg)
    try:
        client.warm()
    except LlmClientError as exc:
        msg = f"warm failed for {tag!r}: {exc}"
        raise PlaygroundSetupError(msg) from exc
    return True


def ensure_model_ready(  # noqa: PLR0913  # setup knobs: pull/wait/warm/poll/timeout/sleep
    client: LlmClient,
    model_id: str,
    *,
    pull_if_missing: bool = True,
    wait: bool = True,
    warm: bool = True,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    timeout_s: float = DEFAULT_PULL_TIMEOUT_S,
    sleep: Callable[[float], None] = time.sleep,
) -> ModelReadyResult:
    """Ensure ``model_id`` is staged on the playground volume; optionally warm it.

    Parameters
    ----------
    client : LlmClient
        Client whose base URL targets playground (or compatible) list/pull/warm.
    model_id : str
        Playground model tag (HF-mapped; see ``resolve_hf_repo``).
    pull_if_missing : bool
        When True, enqueue ``POST /models/ollama/pull`` if not yet available.
    wait : bool
        When True after a pull, poll list until available or ``timeout_s``.
    warm : bool
        When True, POST ``/warm`` once the model is available.
    poll_interval_s : float
        Seconds between list polls while waiting for a pull.
    timeout_s : float
        Max wait after pull before failing.
    sleep : callable
        Sleep function (injectable for tests).

    Returns:
    -------
    ModelReadyResult
        Pull/warm outcome for the requested tag.

    Raises:
    ------
    PlaygroundSetupError
        When the model is missing and pull is disabled, pull/wait times out,
        or HTTP calls fail.
    """
    tag = model_id.strip()
    if not tag:
        msg = "model_id must be a non-empty playground model tag"
        raise PlaygroundSetupError(msg)

    was_available, pulled, job_id = _pull_if_needed(
        client,
        tag,
        pull_if_missing=pull_if_missing,
        wait=wait,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        sleep=sleep,
    )
    available = model_is_available(
        _list_or_raise(client, context=f" after setup for {tag!r}"),
        tag,
    )
    warmed = _warm_if_requested(client, tag, available=available, warm=warm)
    return ModelReadyResult(
        model_id=tag,
        was_available=was_available,
        pulled=pulled,
        job_id=job_id,
        warmed=warmed,
        available=available,
    )


def _wait_until_available(
    client: LlmClient,
    model_id: str,
    *,
    poll_interval_s: float,
    timeout_s: float,
    sleep: Callable[[float], None],
) -> None:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            listing = client.list_models()
        except LlmClientError as exc:
            msg = f"list_models failed while waiting for {model_id!r}: {exc}"
            raise PlaygroundSetupError(msg) from exc
        if model_is_available(listing, model_id):
            return
        if time.monotonic() >= deadline:
            msg = f"timed out after {timeout_s:.0f}s waiting for {model_id!r} to become available"
            raise PlaygroundSetupError(msg)
        sleep(poll_interval_s)
