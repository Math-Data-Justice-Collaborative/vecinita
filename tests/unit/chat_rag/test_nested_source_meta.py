"""T110.4 — ChatRAG nested source metadata on browse + ask Source (F61 / AC-SC11)."""

from __future__ import annotations

from uuid import uuid4

from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.chat_rag import DocumentBrowseItem, Source


def test_document_browse_item_accepts_nested_source_fields() -> None:
    """Browse item schema carries nested source fields (no ChatRAG UI)."""
    item = DocumentBrowseItem(
        document_id=uuid4(),
        title="Guide",
        url="https://tree.example.com/guides/a.html",
        language="en",
        tags=[],
        source_domain="tree.example.com",
        source_path="/guides",
        parent_url="https://tree.example.com/guides/",
        canonical_url="https://tree.example.com/guides/a.html",
    )
    assert item.source_domain == "tree.example.com"
    assert item.source_path == "/guides"


def test_ask_source_and_retrieved_chunk_carry_nested_fields() -> None:
    """Ask Source + RetrievedChunk accept nested metadata for ChatRAG backend."""
    chunk = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="body",
        score=0.9,
        title="Guide",
        url="https://tree.example.com/guides/a.html",
        language="en",
        source_domain="tree.example.com",
        source_path="/guides",
        parent_url="https://tree.example.com/guides/",
        canonical_url="https://tree.example.com/guides/a.html",
    )
    source = Source(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        title=chunk.title,
        url=chunk.url,
        score=chunk.score,
        source_domain=chunk.source_domain,
        source_path=chunk.source_path,
        parent_url=chunk.parent_url,
        canonical_url=chunk.canonical_url,
    )
    assert source.source_domain == "tree.example.com"
    assert source.source_path == "/guides"
    assert source.canonical_url == "https://tree.example.com/guides/a.html"
