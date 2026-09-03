"""Unit: DocumentUpsert rejects NUL bytes in body_text (BUG-2026-09-03)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.internal_write import DocumentUpsert


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
