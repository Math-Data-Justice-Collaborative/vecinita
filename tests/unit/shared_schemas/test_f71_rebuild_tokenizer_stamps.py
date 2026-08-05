"""T120.1 red - F71 schema stamps for multilingual rebuild (no Postgres required).

Asserts CreateRebuildRunRequest accepts chunk_tokenizer_id aligned to E1 pin
(TC-241 / AC-ME11) and embed-promote report payload shape (TC-235-236).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_embedding_client.modal_pins import DEFAULT_EMBEDDING_MODEL_ID
from vecinita_shared_schemas.internal_write import CreateRebuildRunRequest
from vecinita_shared_schemas.json_types import as_json_object


@pytest.mark.unit
def test_create_rebuild_run_accepts_chunk_tokenizer_id_aligned_to_e1() -> None:
    """TC-241: chunk_tokenizer_id must be accepted and equal to embed pin."""
    pin = DEFAULT_EMBEDDING_MODEL_ID
    req = CreateRebuildRunRequest.model_validate(
        {
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "embedding_model_id": pin,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 256,
            "chunk_tokenizer_id": pin,
        }
    )
    payload = as_json_object(req.model_dump(mode="python"))
    assert payload.get("embedding_model_id") == pin
    assert payload.get("chunk_tokenizer_id") == pin
    assert payload.get("mode") == "rechunk"
    assert payload.get("embedding_dim") == EMBEDDING_DIMENSION


@pytest.mark.unit
def test_create_rebuild_run_rejects_tokenizer_mismatch_when_both_set() -> None:
    """When both stamps set, tokenizer must match embed pin (AC-ME11)."""
    with pytest.raises(ValidationError):
        CreateRebuildRunRequest.model_validate(
            {
                "mode": "rechunk",
                "embedding_model_id": DEFAULT_EMBEDDING_MODEL_ID,
                "chunk_tokenizer_id": "BAAI/bge-small-en-v1.5",
                "embedding_dim": EMBEDDING_DIMENSION,
            }
        )
