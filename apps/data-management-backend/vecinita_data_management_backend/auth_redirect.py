"""Auth redirect URL builder for GoTrue invite/recovery (EV-007 F35, ADR-032 §2-3)."""

from __future__ import annotations

import os
from typing import Final, Literal
from urllib.parse import urlparse

AuthCallbackPath = Literal["accept-invite", "reset-password"]

_ADMIN_FRONTEND_ENV: Final = "VECINITA_ADMIN_FRONTEND_URL"


class AdminRedirectConfigError(RuntimeError):
    """Raised when the admin frontend origin env is missing or invalid."""


def admin_frontend_origin_from_env() -> str:
    """Return configured admin SPA origin without trailing slash."""
    raw = os.environ.get(_ADMIN_FRONTEND_ENV, "").strip()
    if not raw:
        msg = f"{_ADMIN_FRONTEND_ENV} is not set"
        raise AdminRedirectConfigError(msg)
    return raw.rstrip("/")


def build_auth_redirect_path(origin: str, path: AuthCallbackPath) -> str:
    """Build a GoTrue ``redirect_to`` URL for invite or recovery emails."""
    base = origin.rstrip("/")
    parsed = urlparse(base)
    if not parsed.scheme or not parsed.netloc:
        msg = f"Invalid admin frontend origin: {origin!r}"
        raise AdminRedirectConfigError(msg)
    if path not in ("accept-invite", "reset-password"):
        msg = f"Invalid auth callback path: {path!r}"
        raise AdminRedirectConfigError(msg)
    return f"{base}/{path}"
