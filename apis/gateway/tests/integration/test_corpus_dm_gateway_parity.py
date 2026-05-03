"""Integration: DM-style corpus rows remain parity-compatible in gateway projection."""

from __future__ import annotations

import pytest

from src.api import router_documents

pytestmark = pytest.mark.integration


def test_dm_projection_fields_survive_gateway_merge() -> None:
    dm_row = router_documents._normalize_public_source(
        {
            "id": "doc-a",
            "source_url": "https://example.org/a",
            "title": "A",
            "metadata": {
                "resource_type": "document",
                "format": "HTML",
                "language": "en",
                "organization": "Vecinita",
                "embedding_status": "completed",
                "source_of_truth": "postgres",
                "canonical_visibility_updated_at": "2026-01-01T00:00:00.000Z",
                "tags": ["community"],
            },
            "total_chunks": 4,
        }
    )
    gateway_row = router_documents._normalize_public_source(
        {
            "source_url": "https://example.org/b",
            "title": "B",
            "metadata": {"source_of_truth": "postgres", "tags": ["housing"]},
            "total_chunks": 2,
        }
    )

    merged = router_documents._merge_sources_by_url([dm_row], [gateway_row])
    assert [entry["url"] for entry in merged] == ["https://example.org/a", "https://example.org/b"]
    assert merged[0]["source_of_truth"] == "postgres"
    assert merged[0]["resource_type"] == "document"
