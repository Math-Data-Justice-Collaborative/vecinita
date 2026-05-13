"""Contract: gateway documents projection preserves canonical corpus fields."""

from __future__ import annotations

import pytest

from src.api import router_documents

pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_normalize_public_source_includes_dm_parity_fields() -> None:
    row = {
        "id": "doc-001",
        "source_url": "https://example.org/resource",
        "title": "Resource",
        "description": "Test resource",
        "metadata": {
            "resource_type": "document",
            "format": "PDF",
            "organization": "Vecinita",
            "embedding_status": "completed",
            "source_of_truth": "postgres",
            "canonical_visibility_updated_at": "2026-01-01T00:00:00.000Z",
            "tags": ["housing"],
        },
        "created_at": "2026-01-01T00:00:00.000Z",
        "updated_at": "2026-01-01T00:00:01.000Z",
    }

    normalized = router_documents._normalize_public_source(row)
    assert normalized["id"] == "doc-001"
    assert normalized["resource_type"] == "document"
    assert normalized["format"] == "PDF"
    assert normalized["organization"] == "Vecinita"
    assert normalized["embedding_status"] == "completed"
    assert normalized["source_of_truth"] == "postgres"
    assert normalized["canonical_visibility_updated_at"] == "2026-01-01T00:00:00.000Z"
