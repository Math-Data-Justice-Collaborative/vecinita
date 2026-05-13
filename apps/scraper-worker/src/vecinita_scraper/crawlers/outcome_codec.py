"""Encode/decode structured crawl outcome payloads in error_message (contract 011)."""

from __future__ import annotations

import json
from typing import Any

from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind

OUTCOME_SCHEMA_VERSION = 1


def encode_outcome_error(
    *,
    failure_category: FailureCategory,
    response_kind: ResponseKind | None = None,
    detail: str | None = None,
    operator_summary: str | None = None,
) -> str:
    """Serialize operator-facing outcome for persistence in error_message."""
    payload: dict[str, Any] = {
        "outcome_schema_version": OUTCOME_SCHEMA_VERSION,
        "failure_category": str(failure_category),
    }
    if response_kind is not None:
        payload["response_kind"] = str(response_kind)
    if detail:
        payload["detail"] = detail[:4000]
    if operator_summary:
        payload["operator_summary"] = operator_summary[:2000]
    return json.dumps(payload, ensure_ascii=False)


def decode_outcome_error(error_message: str | None) -> dict[str, Any] | None:
    """If error_message is JSON outcome payload, return dict; else None."""
    if not error_message or not error_message.strip().startswith("{"):
        return None
    try:
        raw = json.loads(error_message)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        return None
    data: dict[str, Any] = raw
    has_version = data.get("outcome_schema_version") == OUTCOME_SCHEMA_VERSION
    has_category = "failure_category" in data
    if not has_version and not has_category:
        return None
    return data


def merge_legacy_and_outcome(
    legacy_message: str | None,
    *,
    failure_category: FailureCategory | None,
    response_kind: ResponseKind | None,
    operator_summary: str | None,
) -> str | None:
    """Prefer structured JSON when we have a category; keep legacy crawl text in detail."""
    if failure_category is None:
        return legacy_message
    detail = legacy_message if legacy_message else None
    return encode_outcome_error(
        failure_category=failure_category,
        response_kind=response_kind,
        detail=detail,
        operator_summary=operator_summary,
    )
