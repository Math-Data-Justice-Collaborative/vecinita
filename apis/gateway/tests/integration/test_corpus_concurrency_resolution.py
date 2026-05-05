"""Integration: deterministic conflict resolution for near-simultaneous writes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DM_API_BACKEND = (
    Path(__file__).resolve().parents[4] / "apis" / "data-management-api" / "apps" / "backend"
)
if str(_DM_API_BACKEND) not in sys.path:
    sys.path.insert(0, str(_DM_API_BACKEND))

pytestmark = pytest.mark.integration


def test_conflict_resolution_prefers_latest_timestamp() -> None:
    from vecinita_dm_api.corpus_conflict import resolve_corpus_write_conflict

    existing = {"document_id": "doc-1", "updated_at": "2026-01-01T00:00:01+00:00"}
    incoming = {"document_id": "doc-1", "updated_at": "2026-01-01T00:00:02+00:00"}
    resolved = resolve_corpus_write_conflict(existing=existing, incoming=incoming)
    assert resolved["updated_at"] == "2026-01-01T00:00:02+00:00"


def test_conflict_resolution_uses_document_id_tiebreaker() -> None:
    from vecinita_dm_api.corpus_conflict import resolve_corpus_write_conflict

    existing = {"document_id": "doc-a", "updated_at": "2026-01-01T00:00:02+00:00"}
    incoming = {"document_id": "doc-b", "updated_at": "2026-01-01T00:00:02+00:00"}
    resolved = resolve_corpus_write_conflict(existing=existing, incoming=incoming)
    assert resolved["document_id"] == "doc-b"
