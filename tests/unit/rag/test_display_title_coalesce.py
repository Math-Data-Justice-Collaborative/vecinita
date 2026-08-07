"""T125.1 / T125.4 - COALESCE(display_title, title) for packing / citations (TC-249).

[Corpus: feature-list.md §F74]
[Spec: docs/test-plan.md §TC-249]
[Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_rag.display_title import coalesce_document_title
from vecinita_rag.packing import pack_chunks
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit


def test_coalesce_document_title_prefers_display_over_scraped() -> None:
    """AC-SU8: display_title wins when set."""
    assert coalesce_document_title("Neighbor name", "Scraped SEO") == "Neighbor name"


def test_coalesce_document_title_falls_back_to_title_when_display_null() -> None:
    """AC-SU10 / TC-251: null display → scraped title."""
    assert coalesce_document_title(None, "Scraped SEO") == "Scraped SEO"


def test_coalesce_document_title_treats_blank_display_as_unset() -> None:
    """Blank override does not hide scraped title."""
    assert coalesce_document_title("   ", "Scraped SEO") == "Scraped SEO"


def test_pack_chunks_uses_coalesced_title_as_source_header() -> None:
    """TC-249: packing Source header is the display string (already coalesced on chunk)."""
    chunk = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="passage",
        score=0.9,
        title=coalesce_document_title("Neighbor name", "Scraped SEO"),
        url="https://example.org/doc",
        language="en",
    )
    packed = pack_chunks([chunk], mode="p1")
    assert "Source: Neighbor name" in packed
    assert "Scraped SEO" not in packed
