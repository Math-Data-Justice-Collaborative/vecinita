"""TC-337: Internal write OpenAPI publishes FeedbackRequest body on POST /internal/v1/feedback.

[Corpus: api] [Spec: docs/test-plan.md §TC-337]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def _feedback_request_body_schema(openapi: JsonObject) -> JsonObject:
    paths = as_json_object(openapi["paths"])
    op = as_json_object(as_json_object(paths["/internal/v1/feedback"])["post"])
    assert "requestBody" in op, "/internal/v1/feedback missing requestBody in OpenAPI"
    body = as_json_object(op["requestBody"])
    assert body.get("required") is True
    content = as_json_object(body["content"])
    app_json = as_json_object(content["application/json"])
    return as_json_object(app_json["schema"])


def test_openapi_feedback_request_body_documents_category_and_message(
    write_client: TestClient,
) -> None:
    """POST /internal/v1/feedback OpenAPI documents FeedbackRequest (F68 / EV-SAA-D3)."""
    openapi = as_json_object(cast("object", write_client.get("/openapi.json").json()))
    schema = _feedback_request_body_schema(openapi)
    if "$ref" in schema:
        ref = cast("str", schema["$ref"])
        name = ref.rsplit("/", 1)[-1]
        components = as_json_object(openapi["components"])
        schemas = as_json_object(components["schemas"])
        schema = as_json_object(schemas[name])
    required = cast("list[str]", schema.get("required", []))
    properties = as_json_object(schema["properties"])
    assert "category" in required
    assert "message" in required
    assert "category" in properties
    message = as_json_object(properties["message"])
    assert message["type"] == "string"
    assert message.get("minLength") == 1
