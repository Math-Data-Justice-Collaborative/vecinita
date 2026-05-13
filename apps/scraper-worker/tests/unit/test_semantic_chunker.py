"""Unit tests for semantic chunking."""

from __future__ import annotations

import pytest

from vecinita_scraper.chunkers.semantic_chunker import SemanticChunker
from vecinita_scraper.core.errors import ChunkingError
from vecinita_scraper.core.models import ChunkingConfig


@pytest.mark.unit
def test_semantic_chunker_splits_by_paragraph_boundaries() -> None:
    """Paragraphs should be preserved when they fit within the token budget."""
    chunker = SemanticChunker()
    config = ChunkingConfig(min_size_tokens=100, max_size_tokens=200, overlap_ratio=0.2)
    markdown = " ".join(["first"] * 120) + "\n\n" + " ".join(["second"] * 120)

    chunks = chunker.chunk(markdown, config)

    assert len(chunks) == 2
    assert chunks[0]["text"].startswith("first first")
    assert chunks[1]["text"].startswith("second second")


@pytest.mark.unit
def test_semantic_chunker_rejects_empty_content() -> None:
    """Empty markdown should fail fast."""
    chunker = SemanticChunker()
    config = ChunkingConfig()

    with pytest.raises(ChunkingError):
        chunker.chunk("   ", config)
