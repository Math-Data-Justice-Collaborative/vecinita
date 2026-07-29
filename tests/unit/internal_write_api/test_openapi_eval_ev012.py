"""T83.6 — OpenAPI internal-write EV-012 eval SSE + soft-delete paths."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_OPENAPI = Path(__file__).resolve().parents[3] / "openapi" / "internal-write.yaml"


def _load_spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_OPENAPI.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def test_openapi_eval_run_events_documents_last_event_id() -> None:
    """GET …/eval/runs/{run_id}/events documents Last-Event-ID (TP-S013-04)."""
    paths = as_json_object(_load_spec()["paths"])
    events = as_json_object(paths["/eval/runs/{run_id}/events"])
    get_op = as_json_object(events["get"])
    parameters = cast("list[object]", get_op.get("parameters", []))
    names: set[object] = set()
    for param in parameters:
        names.add(as_json_object(param).get("name"))
    assert "Last-Event-ID" in names
    content = as_json_object(as_json_object(as_json_object(get_op["responses"])["200"])["content"])
    assert "text/event-stream" in content


def test_openapi_eval_run_delete_soft_deletes() -> None:
    """DELETE /eval/runs/{run_id} soft-deletes via deleted_at (TP-S013-05)."""
    paths = as_json_object(_load_spec()["paths"])
    run = as_json_object(paths["/eval/runs/{run_id}"])
    assert "delete" in run
    delete_op = as_json_object(run["delete"])
    summary = str(delete_op.get("summary", "")).lower()
    assert "soft" in summary or "deleted_at" in summary
    responses = as_json_object(delete_op["responses"])
    assert "204" in responses
