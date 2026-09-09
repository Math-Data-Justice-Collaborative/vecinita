"""TC-332 / UX-9: live OpenAPI publishes AskRequest body with required question."""

from __future__ import annotations

from typing import cast

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

pytestmark = pytest.mark.unit


def _ask_request_body_schema(openapi: JsonObject, path: str) -> JsonObject:
    paths = as_json_object(openapi["paths"])
    op = as_json_object(as_json_object(paths[path])["post"])
    assert "requestBody" in op, f"{path} missing requestBody in OpenAPI"
    body = as_json_object(op["requestBody"])
    content = as_json_object(body["content"])
    app_json = as_json_object(content["application/json"])
    return as_json_object(app_json["schema"])


def test_live_openapi_ask_request_body_requires_question() -> None:
    """POST /api/v1/ask OpenAPI documents AskRequest.question (EV-ux-backlog UX-9)."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    client = TestClient(create_app(settings=settings))
    openapi = as_json_object(cast("object", client.get("/openapi.json").json()))

    for path in ("/api/v1/ask", "/api/v1/ask/stream"):
        schema = _ask_request_body_schema(openapi, path)
        # Inline or $ref — resolve properties
        if "$ref" in schema:
            ref = cast("str", schema["$ref"])
            name = ref.rsplit("/", 1)[-1]
            components = as_json_object(openapi["components"])
            schemas = as_json_object(components["schemas"])
            schema = as_json_object(schemas[name])
        required = cast("list[str]", schema.get("required", []))
        properties = as_json_object(schema["properties"])
        assert "question" in required
        assert "question" in properties
        question = as_json_object(properties["question"])
        assert question["type"] == "string"
