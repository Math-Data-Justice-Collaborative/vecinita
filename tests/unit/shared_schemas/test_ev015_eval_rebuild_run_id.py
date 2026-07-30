"""T89.2 — EvalRunCreateRequest accepts optional rebuild_run_id (TP-S017-04 / TC-168)."""

from __future__ import annotations

from uuid import uuid4

from vecinita_shared_schemas.internal_write import EvalRunCreateRequest
from vecinita_shared_schemas.json_types import as_json_object


def test_eval_run_create_request_accepts_optional_rebuild_run_id() -> None:
    """F36-on-shadow: eval enqueue may carry rebuild_run_id (TP-S017-04)."""
    run_id = uuid4()
    req = EvalRunCreateRequest.model_validate({"rebuild_run_id": str(run_id)})
    payload = as_json_object(req.model_dump(mode="python"))
    assert payload.get("rebuild_run_id") == run_id


def test_eval_run_create_request_defaults_rebuild_run_id_none() -> None:
    """Omitting rebuild_run_id keeps live retrieval path."""
    req = EvalRunCreateRequest.model_validate({})
    payload = as_json_object(req.model_dump(mode="python"))
    assert "rebuild_run_id" in payload
    assert payload.get("rebuild_run_id") is None
