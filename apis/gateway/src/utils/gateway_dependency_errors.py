"""Client-safe error messages for gateway dependency failures (Postgres, DNS, etc.)."""

from __future__ import annotations

import re

_RENDER_PG_HOST_RE = re.compile(r"\bdpg-[a-z0-9-]+\b", re.IGNORECASE)


def _strip_internal_hostnames(message: str) -> str:
    """Remove obvious Render internal Postgres hostname tokens from operator-facing text."""
    return _RENDER_PG_HOST_RE.sub("<database-host>", message)


def client_safe_message_for_dependency_failure(exc: BaseException) -> str:
    """
    Map dependency errors (e.g. psycopg2 DNS / connection failures) to a message safe for JSON
    returned to API clients (**FR-002**): no raw internal DNS names.
    """
    raw = str(exc).strip() or "Dependency error"
    lowered = raw.lower()
    sanitized = _strip_internal_hostnames(raw)

    if "could not translate host name" in lowered or "<database-host>" in sanitized:
        return (
            "Database unreachable from this runtime; verify DATABASE_URL / network configuration "
            "with operators (internal hostname references are redacted)."
        )

    if "password authentication failed" in lowered or "authentication failed" in lowered:
        return "Database authentication failed; verify credentials with operators."

    if "could not connect" in lowered or "connection refused" in lowered:
        return "Database connection refused; verify host, port, and network reachability."

    # Default: redact known internal patterns but keep a short generic tail for operators.
    if "dpg-" in lowered:
        return _strip_internal_hostnames(
            "Database error (details redacted for client response; see gateway logs)."
        )
    return sanitized[:500] if len(sanitized) > 500 else sanitized
