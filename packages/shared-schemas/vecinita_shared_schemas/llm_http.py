"""Shared LLM HTTP config resolver (TP-S010-20 / RD-163)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Final

logger = logging.getLogger(__name__)

_ENV_LLM_URL: Final[str] = "VECINITA_MODAL_LLM_URL"
_ENV_OLLAMA_URL: Final[str] = "VECINITA_MODAL_OLLAMA_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"
_ENV_LLM_MODEL_ID: Final[str] = "VECINITA_LLM_MODEL_ID"
_ENV_OLLAMA_MODEL_ID: Final[str] = "VECINITA_OLLAMA_MODEL_ID"
_DEFAULT_TIMEOUT_S: Final[float] = 120.0


class LlmHttpConfigError(ValueError):
    """LLM base URL / proxy key / timeout could not be resolved."""


@dataclass(frozen=True, slots=True)
class LlmHttpConfig:
    """Resolved Modal LLM HTTP settings shared by ``LlmClient``."""

    base_url: str
    proxy_key: str | None
    timeout: float
    model_id: str | None


def resolve_llm_http_config(
    *,
    base_url: str | None = None,
    proxy_key: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT_S,
    model_id: str | None = None,
    require_proxy_key: bool = False,
) -> LlmHttpConfig:
    """Resolve LLM URL, proxy key, timeout, and model id from args or env."""
    legacy_ollama = os.environ.get(_ENV_OLLAMA_URL)
    if legacy_ollama:
        logger.warning(
            "%s is deprecated (ADR-037); use %s only",
            _ENV_OLLAMA_URL,
            _ENV_LLM_URL,
        )
    resolved_url = base_url or os.environ.get(_ENV_LLM_URL) or legacy_ollama
    if not resolved_url:
        msg = f"{_ENV_LLM_URL} or base_url is required"
        raise LlmHttpConfigError(msg)

    resolved_key = proxy_key if proxy_key is not None else os.environ.get(_ENV_PROXY_KEY)
    if require_proxy_key and not resolved_key:
        msg = f"{_ENV_PROXY_KEY} is required"
        raise LlmHttpConfigError(msg)

    resolved_model = (
        model_id
        if model_id is not None
        else (os.environ.get(_ENV_LLM_MODEL_ID) or os.environ.get(_ENV_OLLAMA_MODEL_ID))
    )
    return LlmHttpConfig(
        base_url=resolved_url.rstrip("/"),
        proxy_key=resolved_key,
        timeout=timeout,
        model_id=resolved_model,
    )
