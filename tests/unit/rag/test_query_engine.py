"""Query engine helpers with mocked retrieval."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_rag.engine import (
    answer_from_chunks,
)
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit


def test_answer_from_chunks_uses_top_chunk_text() -> None:
    """Test answer from chunks uses top chunk text."""
    chunk = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="Food pantry hours are posted on Monday.",
        score=0.9,
        title="Community resources",
        url="fixture://corpus/en/community-resources.md",
        language="en",
    )
    result = answer_from_chunks("food pantry hours?", [chunk])
    assert result.language == "en"
    assert "Food pantry" in result.answer
    assert len(result.sources) == 1
