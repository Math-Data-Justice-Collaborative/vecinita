"""T89.7 — OpenAPI promote + eval rebuild_run_id (TP-S017-04/06 / F41)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "internal-write.yaml"


def _load_spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def test_openapi_rebuild_promote_path_and_response() -> None:
    """POST /rebuild/{rebuild_run_id}/promote returns TP-S017-06 shape."""
    spec = _load_spec()
    paths = as_json_object(spec["paths"])
    assert "/rebuild/{rebuild_run_id}/promote" in paths
    promote = as_json_object(paths["/rebuild/{rebuild_run_id}/promote"])
    post = as_json_object(promote["post"])
    assert post.get("operationId") == "promoteRebuildRun"
    responses = as_json_object(post["responses"])
    assert "200" in responses
    assert "404" in responses
    assert "409" in responses

    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    assert "RebuildPromoteResponse" in schemas
    body = as_json_object(schemas["RebuildPromoteResponse"])
    required = set(cast("list[str]", body["required"]))
    assert required == {
        "promoted",
        "rebuild_run_id",
        "chunks_promoted",
        "documents_promoted",
    }
    props = as_json_object(body["properties"])
    assert as_json_object(props["promoted"]).get("type") == "boolean"
    assert as_json_object(props["rebuild_run_id"]).get("format") == "uuid"
    assert as_json_object(props["chunks_promoted"]).get("type") == "integer"
    assert as_json_object(props["documents_promoted"]).get("type") == "integer"


def test_openapi_eval_run_create_accepts_rebuild_run_id() -> None:
    """EvalRunCreateRequest.rebuild_run_id optional UUID (TP-S017-04 / TC-168)."""
    spec = _load_spec()
    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    create = as_json_object(schemas["EvalRunCreateRequest"])
    props = as_json_object(create["properties"])
    assert "rebuild_run_id" in props
    field = as_json_object(props["rebuild_run_id"])
    assert field.get("format") == "uuid"
    assert field.get("nullable") is True
