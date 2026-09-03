"""Unit: DocumentUpsert rejects NUL bytes in body_text (BUG-2026-09-03)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.internal_write import ChunkUpsert, DocumentUpsert


def test_document_upsert_rejects_nul_in_body_text() -> None:
    """Postgres cannot store NUL; validate before INSERT."""
    with pytest.raises(ValidationError) as exc_info:
        _ = DocumentUpsert.model_validate(
            {
                "url": "https://drive.google.com/file/d/x/view",
                "language": "en",
                "content_hash": "abc",
                "body_text": "%PDF-1.4\x00binary",
                "chunks": [],
            }
        )
    assert "NUL" in str(exc_info.value)


def test_chunk_upsert_rejects_nul_in_text() -> None:
    """Chunk text with NUL must fail validation before upsert."""
    with pytest.raises(ValidationError) as exc_info:
        _ = ChunkUpsert.model_validate(
            {
                "chunk_index": 0,
                "text": "hello\x00world",
                "embedding": [0.0] * 384,
            }
        )
    assert "NUL" in str(exc_info.value)
