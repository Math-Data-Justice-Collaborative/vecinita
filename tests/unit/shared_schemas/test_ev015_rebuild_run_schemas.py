"""T88.4 — rebuild_runs create/update schemas (TP-S017-02)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.internal_write import (
    CreateRebuildRunRequest,
    CreateRebuildRunResponse,
    UpdateRebuildRunRequest,
)
from vecinita_shared_schemas.json_types import as_json_object


def test_create_rebuild_run_request_accepts_modes_and_stamps() -> None:
    """CreateRebuildRunRequest carries mode, dry_run, force, and version stamps."""
    job_id = uuid4()
    req = CreateRebuildRunRequest.model_validate(
        {
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "running",
            "job_id": str(job_id),
            "embedding_model_id": "BAAI/bge-small-en-v1.5",
            "embedding_dim": 384,
            "chunk_size_tokens": 64,
        }
    )
    payload = as_json_object(req.model_dump(mode="python"))
    assert payload.get("mode") == "rechunk"
    assert payload.get("dry_run") is True
    assert payload.get("force") is True
    assert payload.get("job_id") == job_id


def test_create_rebuild_run_request_rejects_unknown_mode() -> None:
    """Invalid rebuild mode is rejected at the schema boundary."""
    with pytest.raises(ValidationError):
        CreateRebuildRunRequest.model_validate({"mode": "reindex", "dry_run": True})


def test_create_rebuild_run_response_requires_id() -> None:
    """CreateRebuildRunResponse exposes rebuild_run_id for shadow dual-write."""
    run_id = uuid4()
    resp = CreateRebuildRunResponse.model_validate(
        {"rebuild_run_id": str(run_id), "status": "running"}
    )
    assert resp.rebuild_run_id == run_id
    assert resp.status == "running"


def test_update_rebuild_run_request_status_lifecycle() -> None:
    """UpdateRebuildRunRequest accepts terminal and promoted statuses."""
    for status in ("completed", "failed", "promoted"):
        req = UpdateRebuildRunRequest.model_validate({"status": status})
        assert as_json_object(req.model_dump(mode="python")).get("status") == status
