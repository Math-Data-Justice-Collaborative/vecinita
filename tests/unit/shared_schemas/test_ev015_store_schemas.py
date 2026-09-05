"""T86.3 — F41 shared schemas for document store + promote (ADR-040 / TP-S017-06)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    RebuildPromoteResponse,
)

_EMBEDDING_DIM = 384
_CHUNKS_PROMOTED = 12
_DOCUMENTS_PROMOTED = 3
_CHUNK_SIZE_TOKENS = 256


def test_batch_upsert_accepts_body_text_and_version_stamps() -> None:
    """DocumentUpsert may include body_text and embedding/chunk stamps (F41)."""
    embedding = [0.0] * _EMBEDDING_DIM
    model = BatchUpsertRequest.model_validate(
        {
            "documents": [
                {
                    "url": "https://example.com/doc",
                    "body_text": "normalized scrape body",
                    "embedding_model_id": "fastembed-default",
                    "embedding_dim": _EMBEDDING_DIM,
                    "chunk_size_tokens": _CHUNK_SIZE_TOKENS,
                    "rebuild_run_id": str(uuid4()),
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "chunk",
                            "embedding": embedding,
                        }
                    ],
                }
            ]
        }
    )
    doc = model.documents[0]
    assert doc.body_text == "normalized scrape body"
    assert doc.embedding_dim == _EMBEDDING_DIM
    assert doc.chunk_size_tokens == _CHUNK_SIZE_TOKENS
    assert doc.rebuild_run_id is not None


def test_rebuild_promote_response_shape() -> None:
    """Promote response matches TP-S017-06 OpenAPI lock."""
    run_id = uuid4()
    model = RebuildPromoteResponse.model_validate(
        {
            "promoted": True,
            "rebuild_run_id": str(run_id),
            "chunks_promoted": _CHUNKS_PROMOTED,
            "documents_promoted": _DOCUMENTS_PROMOTED,
        }
    )
    assert model.promoted is True
    assert model.rebuild_run_id == run_id
    assert model.chunks_promoted == _CHUNKS_PROMOTED
    assert model.documents_promoted == _DOCUMENTS_PROMOTED


def test_rebuild_promote_response_rejects_negative_counts() -> None:
    """Promote counts must be non-negative."""
    with pytest.raises(ValidationError):
        _ = RebuildPromoteResponse.model_validate(
            {
                "promoted": True,
                "rebuild_run_id": str(uuid4()),
                "chunks_promoted": -1,
                "documents_promoted": 0,
            }
        )
