"""Shared LLM HTTP config resolver (TP-S010-20 / RD-163).

T77.1 red-phase stub: public types only. T77.3 implements resolution.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    timeout: float = 120.0,
    model_id: str | None = None,
    require_proxy_key: bool = False,
) -> LlmHttpConfig:
    """Resolve LLM URL, proxy key, timeout, and model id from args or env.

    Implemented in T77.3 (TP-S010-20).
    """
    del base_url, proxy_key, timeout, model_id, require_proxy_key
    msg = "resolve_llm_http_config is not implemented yet (T77.3)"
    raise NotImplementedError(msg)
