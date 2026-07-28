"""BUG-2026-07-28 / #112 — Admin GET /documents must declare server-side pagination."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_object_get, json_str

_REPO_ROOT = Path(__file__).resolve().parents[2]
_OPENAPI = _REPO_ROOT / "openapi" / "internal-write.yaml"


def test_list_documents_openapi_declares_paginated_contract() -> None:
    """Openapi GET /documents must expose page/page_size and a page envelope.

    Regression for issue #112 — admin CorpusList needs server-side pagination
    (mirror Users / public browse). Asserted against OpenAPI so the bug suite
    stays runnable without a local Postgres.
    """
    loaded = cast("object", yaml.safe_load(_OPENAPI.read_text(encoding="utf-8")))
    spec = as_json_object(loaded)
    paths = as_json_object(spec["paths"])
    documents = as_json_object(paths["/documents"])
    get_op = as_json_object(documents["get"])

    params = json_list(get_op, "parameters") if "parameters" in get_op else []
    names: set[str] = set()
    for param in params:
        obj = as_json_object(param)
        if "name" in obj:
            names.add(json_str(obj, "name"))
    assert "page" in names, "GET /documents must accept page query param"
    assert "page_size" in names, "GET /documents must accept page_size query param"

    responses = as_json_object(get_op["responses"])
    ok = as_json_object(responses["200"])
    content = as_json_object(ok["content"])
    app_json = as_json_object(content["application/json"])
    schema = as_json_object(app_json["schema"])
    ref = json_str(schema, "$ref")
    assert ref.endswith("/DocumentListPage"), f"expected DocumentListPage ref, got {ref}"

    components = as_json_object(spec["components"])
    schemas = as_json_object(components["schemas"])
    page_schema = as_json_object(schemas["DocumentListPage"])
    props = json_object_get(page_schema, "properties")
    for key in ("items", "page", "page_size", "total"):
        assert key in props, f"paginated schema missing '{key}'"
