"""T82.5 — OpenAPI data-management EV-012 Job/JobOptions sync (TP-S013-01)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "data-management.yaml"


def _load_spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def _job_options_schema(spec: JsonObject) -> JsonObject:
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    return as_json_object(schemas["JobOptions"])


def test_openapi_job_options_include_eval_and_document_fields() -> None:
    """CreateJobRequest.options must declare job_type, document_id, eval_run_id."""
    spec = _load_spec()
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    create_req = as_json_object(schemas["CreateJobRequest"])
    props = as_json_object(create_req["properties"])
    options_ref = as_json_object(props["options"])
    assert options_ref.get("$ref") == "#/components/schemas/JobOptions"

    option_props = as_json_object(_job_options_schema(spec)["properties"])
    assert "job_type" in option_props
    job_type = as_json_object(option_props["job_type"])
    assert set(cast("list[str]", job_type["enum"])) == {"ingest", "retag", "eval"}
    assert "document_id" in option_props
    assert "eval_run_id" in option_props
    assert "chunk_size_tokens" in option_props


def test_openapi_create_job_allows_empty_urls_for_non_ingest() -> None:
    """Urls must not require minItems=1 (retag/eval use options instead)."""
    spec = _load_spec()
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    create_req = as_json_object(schemas["CreateJobRequest"])
    props = as_json_object(create_req["properties"])
    urls = as_json_object(props["urls"])
    required = cast("list[str]", create_req.get("required", []))
    assert "urls" not in required
    assert urls.get("minItems", 0) in (0, None)


def test_openapi_jobs_events_documents_last_event_id() -> None:
    """GET /jobs/events documents Last-Event-ID reconnect header (TC-148)."""
    spec = _load_spec()
    paths = as_json_object(spec["paths"])
    events = as_json_object(paths["/jobs/events"])
    get_op = as_json_object(events["get"])
    parameters = cast("list[object]", get_op.get("parameters", []))
    names: set[object] = set()
    for param in parameters:
        names.add(as_json_object(param).get("name"))
    assert "Last-Event-ID" in names
