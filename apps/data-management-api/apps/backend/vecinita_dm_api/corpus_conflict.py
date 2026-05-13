"""Deterministic conflict-resolution helper for corpus writes."""

from __future__ import annotations

from typing import Any


def resolve_corpus_write_conflict(
    *, existing: dict[str, Any], incoming: dict[str, Any]
) -> dict[str, Any]:
    existing_ts = str(existing.get("updated_at") or "")
    incoming_ts = str(incoming.get("updated_at") or "")
    if incoming_ts > existing_ts:
        return incoming
    if incoming_ts < existing_ts:
        return existing
    return incoming if str(incoming.get("document_id", "")) >= str(existing.get("document_id", "")) else existing
