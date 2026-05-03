"""Strip characters PostgreSQL ``json``/``jsonb`` cannot store (notably U+0000)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_NUL = "\u0000"


def sanitize_postgres_text(value: str) -> str:
    """Remove NUL bytes from text bound for Postgres ``text``/``varchar`` columns."""
    return value.replace(_NUL, "") if _NUL in value else value


def sanitize_postgres_json_payload(value: Any) -> Any:
    """Recursively remove NUL from string keys and values for ``json``/``jsonb`` parameters."""
    if isinstance(value, str):
        return sanitize_postgres_text(value)
    if isinstance(value, Mapping):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            new_key = sanitize_postgres_text(key) if isinstance(key, str) else key
            out[new_key] = sanitize_postgres_json_payload(item)
        return out
    if isinstance(value, tuple):
        return tuple(sanitize_postgres_json_payload(item) for item in value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_postgres_json_payload(item) for item in value]
    if isinstance(value, bytes):
        return sanitize_postgres_text(value.decode("utf-8", errors="replace"))
    if isinstance(value, bytearray):
        return sanitize_postgres_text(bytes(value).decode("utf-8", errors="replace"))
    return value
