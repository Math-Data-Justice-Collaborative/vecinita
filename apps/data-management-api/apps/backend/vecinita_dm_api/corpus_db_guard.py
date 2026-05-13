"""Canonical DATABASE_URL guard for data-management API runtime."""

from __future__ import annotations

import os
from urllib.parse import urlparse

_DISALLOWED_TOKENS = ("mock", "placeholder", "example", "changeme")
_ALLOWED_SCHEMES = {"postgres", "postgresql"}


def validate_canonical_database_url(*, service_name: str, strict: bool | None = None) -> str:
    strict_mode = (
        strict if strict is not None else bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))
    )
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if not database_url:
        if strict_mode:
            raise RuntimeError(f"{service_name}: DATABASE_URL must be set for canonical corpus access.")
        return database_url

    parsed = urlparse(database_url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise RuntimeError(f"{service_name}: DATABASE_URL must be a canonical postgres connection.")

    lower = database_url.lower()
    if strict_mode and any(token in lower for token in _DISALLOWED_TOKENS):
        raise RuntimeError(
            f"{service_name}: DATABASE_URL must be a canonical postgres connection "
            "without mock/placeholder/example markers."
        )
    return database_url
