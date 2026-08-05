"""T121.1 red — F71 E0 rollback rebuild request contract (TC-239 / AC-ME9).

No Postgres required. Encodes the F41 runbook path: rollback is a **new** rechunk
rebuild stamped with LEGACY_E0 (not re-promote of an already-promoted E1 run).

[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-239]
[Spec: docs/acceptance-criteria.md §AC-ME9]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    LEGACY_E0_EMBEDDING_MODEL_ID,
)
from vecinita_shared_schemas.internal_write import CreateRebuildRunRequest
from vecinita_shared_schemas.json_types import as_json_object

_E1 = DEFAULT_EMBEDDING_MODEL_ID
_E0 = LEGACY_E0_EMBEDDING_MODEL_ID


@pytest.mark.unit
def test_tc239_e0_rollback_create_rebuild_uses_legacy_pin_and_matching_tokenizer() -> None:
    """TC-239 / AC-ME9: E0 rollback rebuild stamps LEGACY_E0 on embed + tokenizer."""
    assert _E0 == "BAAI/bge-small-en-v1.5"
    assert _E0 != _E1

    req = CreateRebuildRunRequest.model_validate(
        {
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "embedding_model_id": _E0,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 256,
            "chunk_tokenizer_id": _E0,
        }
    )
    payload = as_json_object(req.model_dump(mode="python"))
    assert payload.get("mode") == "rechunk"
    assert payload.get("dry_run") is True
    assert payload.get("force") is True
    assert payload.get("status") == "running"
    assert payload.get("embedding_model_id") == _E0
    assert payload.get("embedding_dim") == EMBEDDING_DIMENSION
    assert payload.get("chunk_size_tokens") == 256
    assert payload.get("chunk_tokenizer_id") == _E0
    assert payload.get("job_id") is None


@pytest.mark.unit
def test_tc239_e0_rollback_rejects_tokenizer_mismatched_to_e0_pin() -> None:
    """Rollback rebuild must keep tokenizer aligned to E0 pin (AC-ME11 on rollback path)."""
    with pytest.raises(ValidationError):
        CreateRebuildRunRequest.model_validate(
            {
                "mode": "rechunk",
                "embedding_model_id": _E0,
                "chunk_tokenizer_id": _E1,
                "embedding_dim": EMBEDDING_DIMENSION,
            }
        )
