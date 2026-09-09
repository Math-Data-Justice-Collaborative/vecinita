"""TC-333: OpenAPI publishes FeedbackRequest body and error responses.

[Corpus: api] [Spec: docs/test-plan.md §TC-333]
[Corpus: feature-list.md §F68]
"""

from __future__ import annotations

from typing import cast

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_shared_schemas.json_types import as_json_object

pytestmark = pytest.mark.unit


def _client() -> TestClient:
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    return TestClient(create_app(settings=settings))


def test_openapi_feedback_request_body_requires_category_and_message() -> None:
    """POST /api/v1/feedback OpenAPI documents FeedbackRequest (EV-staging-api-adversarial)."""
    openapi = as_json_object(cast("object", _client().get("/openapi.json").json()))
    paths = as_json_object(openapi["paths"])
    op = as_json_object(as_json_object(paths["/api/v1/feedback"])["post"])
    assert "requestBody" in op
    body = as_json_object(op["requestBody"])
    content = as_json_object(body["content"])
    schema = as_json_object(as_json_object(content["application/json"])["schema"])
    if "$ref" in schema:
        ref = cast("str", schema["$ref"])
        name = ref.rsplit("/", 1)[-1]
        schemas = as_json_object(as_json_object(openapi["components"])["schemas"])
        schema = as_json_object(schemas[name])
    required = cast("list[str]", schema.get("required", []))
    properties = as_json_object(schema["properties"])
    assert "category" in required
    assert "message" in required
    assert "category" in properties
    assert "message" in properties
    assert schema.get("additionalProperties") is False


def test_openapi_feedback_documents_400_and_503() -> None:
    """Feedback OpenAPI lists 400/503 alongside 201 (Schemathesis status conformance)."""
    openapi = as_json_object(cast("object", _client().get("/openapi.json").json()))
    op = as_json_object(
        as_json_object(as_json_object(openapi["paths"])["/api/v1/feedback"])["post"]
    )
    responses = as_json_object(op["responses"])
    assert "201" in responses
    assert "400" in responses
    assert "503" in responses
