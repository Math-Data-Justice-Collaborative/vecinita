"""Integration: projection reconciliation recovers after partial failures."""

from __future__ import annotations

import pytest

from src.services.corpus.corpus_projection_service import reconcile_projection_sources

pytestmark = pytest.mark.integration


def test_reconcile_projection_prefers_latest_source_entry() -> None:
    stale = {
        "url": "https://example.org/resource",
        "source_of_truth": "postgres",
        "canonical_visibility_updated_at": "2026-01-01T00:00:00+00:00",
    }
    recovered = {
        "url": "https://example.org/resource",
        "source_of_truth": "postgres",
        "canonical_visibility_updated_at": "2026-01-01T00:00:20+00:00",
    }

    reconciled = reconcile_projection_sources([stale, recovered])
    assert len(reconciled) == 1
    assert reconciled[0]["canonical_visibility_updated_at"] == "2026-01-01T00:00:20+00:00"
