"""Centralized service endpoint resolution for Vecinita backend.

Single source of truth for all cross-service URLs, proxy flags, and
CORS origins.  Import from here — never call os.getenv() for
cross-service endpoints directly in routers or handlers.

Endpoints are resolved once at import time using the normalisation logic
in ``src.config`` so all services observe the same Render-aware URL
rewriting in a consistent place.
"""

from __future__ import annotations

import logging
import os

from src.config import (
    EMBEDDING_SERVICE_URL,
    OLLAMA_BASE_URL,
    _normalize_internal_service_url,
    _running_on_render,
)

# ---------------------------------------------------------------------------
# Modal proxy (model, embedding, scraper)
# ---------------------------------------------------------------------------

#: Model endpoint.  On Render this is always the modal-proxy /model path.
MODEL_ENDPOINT: str = OLLAMA_BASE_URL or "http://vecinita-modal-proxy-v1:10000/model"

#: Embedding endpoint.  On Render this is always the modal-proxy /embedding path.
EMBEDDING_ENDPOINT: str = EMBEDDING_SERVICE_URL

#: Scraper/job endpoint through the proxy.
SCRAPER_ENDPOINT: str = _normalize_internal_service_url(
    os.getenv("VECINITA_SCRAPER_API_URL") or os.getenv("SCRAPER_SERVICE_URL"),
    fallback_url="http://vecinita-modal-proxy-v1:10000/jobs",
)

# ---------------------------------------------------------------------------
# Internal service routing
# ---------------------------------------------------------------------------

#: URL of the agent service (used by the gateway router to proxy /ask).
AGENT_SERVICE_URL: str = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Proxy auth
# ---------------------------------------------------------------------------

#: Shared proxy auth token for agent→modal-proxy requests.
PROXY_AUTH_TOKEN: str | None = os.getenv("PROXY_AUTH_TOKEN")

# ---------------------------------------------------------------------------
# Strict-mode flags
# ---------------------------------------------------------------------------


def is_render_strict_mode() -> bool:
    """Return True when both AGENT_ENFORCE_PROXY and RENDER_REMOTE_INFERENCE_ONLY are enabled.

    In strict mode no silent fallback to local model/embedding is permitted.
    Startup should abort rather than fall back.
    """

    def _truthy(k: str) -> bool:
        return os.getenv(k, "").lower() in {"1", "true", "yes", "on"}

    return _truthy("AGENT_ENFORCE_PROXY") and _truthy("RENDER_REMOTE_INFERENCE_ONLY")


def is_render() -> bool:
    """Detect Render platform at runtime (not cached — safe to call per-request)."""
    return _running_on_render()


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


def get_allowed_origins() -> list[str]:
    """Parse ALLOWED_ORIGINS env var into a list of origin strings.

    Falls back to ``["*"]`` when not set so development environments do not
    require explicit configuration.
    """
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.replace(",", " ").split() if o.strip()]


# ---------------------------------------------------------------------------
# Startup summary log
# ---------------------------------------------------------------------------


def log_endpoint_summary(logger: logging.Logger) -> None:
    """Emit a structured startup log of all resolved endpoints and policy flags.

    Call this once during application lifespan startup so operators can
    confirm routing policy in logs without diving into env var lists.
    """
    origins = get_allowed_origins()
    logger.info(
        "service_endpoints_summary "
        "model=%s embedding=%s scraper=%s agent=%s "
        "proxy_token_set=%s strict_mode=%s on_render=%s "
        "allowed_origins=%s",
        MODEL_ENDPOINT,
        EMBEDDING_ENDPOINT,
        SCRAPER_ENDPOINT,
        AGENT_SERVICE_URL,
        bool(PROXY_AUTH_TOKEN),
        is_render_strict_mode(),
        is_render(),
        origins,
    )
