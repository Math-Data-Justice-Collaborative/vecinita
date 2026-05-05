"""Deterministic corpus seed helpers for sync/parity integration tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedCorpusDocument:
    external_id: str
    title: str
    source_url: str
    content: str


def build_seed_corpus_documents(count: int = 30) -> list[SeedCorpusDocument]:
    """Build a stable document set used by SC-001 parity checks."""
    if count < 1:
        raise ValueError("count must be >= 1")
    documents: list[SeedCorpusDocument] = []
    for idx in range(count):
        ordinal = idx + 1
        documents.append(
            SeedCorpusDocument(
                external_id=f"seed-doc-{ordinal:03d}",
                title=f"Seed Corpus Document {ordinal:03d}",
                source_url=f"https://example.org/corpus/{ordinal:03d}",
                content=f"Deterministic corpus body for document {ordinal:03d}.",
            )
        )
    return documents
