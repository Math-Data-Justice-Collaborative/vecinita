"""Canonical DATABASE_URL guardrails for corpus read/write paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

_DISALLOWED_TOKENS = ("mock", "placeholder", "example", "changeme")
_ALLOWED_SCHEMES = {"postgres", "postgresql"}


@dataclass(frozen=True)
class CanonicalDbValidationResult:
    database_url: str
    strict: bool


def _is_strict_mode(explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    # Default to strict on Render/prod-like runtimes, permissive in local dev.
    return bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))


def validate_canonical_database_url(
    *,
    service_name: str,
    strict: bool | None = None,
    database_url: str | None = None,
) -> CanonicalDbValidationResult:
    """Validate canonical DATABASE_URL for corpus-serving services."""
    resolved = (database_url if database_url is not None else os.getenv("DATABASE_URL", "")).strip()
    strict_mode = _is_strict_mode(strict)
    if not resolved:
        if strict_mode:
            raise RuntimeError(
                f"{service_name}: DATABASE_URL must be set for canonical corpus access."
            )
        return CanonicalDbValidationResult(database_url="", strict=False)

    parsed = urlparse(resolved)
    lower_url = resolved.lower()
    is_valid = parsed.scheme in _ALLOWED_SCHEMES and not any(
        token in lower_url for token in _DISALLOWED_TOKENS
    )
    if strict_mode and not is_valid:
        raise RuntimeError(
            f"{service_name}: DATABASE_URL must be a canonical postgres connection "
            "without mock/placeholder/example markers."
        )
    return CanonicalDbValidationResult(database_url=resolved, strict=strict_mode)
