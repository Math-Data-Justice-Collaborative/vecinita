"""TC-337: OpenAPI repo↔live drift helpers.

[Corpus: api] [Corpus: staging] [Spec: docs/test-plan.md §TC-337]
"""

from __future__ import annotations

from typing import cast

import pytest
from scripts.ops.openapi_live_drift import (
    drift_messages,
    normalize_path,
    required_security_scheme_names,
)
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

pytestmark = pytest.mark.unit


def test_normalize_path_strips_servers_prefix() -> None:
    """Repo relative paths join with servers.url; live often uses absolute paths."""
    assert normalize_path("/ask", "/api/v1") == "/api/v1/ask"
    assert normalize_path("/api/v1/ask", "/api/v1") == "/api/v1/ask"
    assert normalize_path("ask", "api/v1") == "/api/v1/ask"


def test_drift_messages_flags_missing_live_request_body() -> None:
    """When repo documents requestBody, live OpenAPI must too (TC-336 class)."""
    repo = as_json_object(
        cast(
            "object",
            {
                "servers": [{"url": "/api/v1"}],
                "paths": {
                    "/ask": {
                        "post": {
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/AskRequest",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ),
    )
    live: JsonObject = as_json_object(
        cast("object", {"paths": {"/api/v1/ask": {"post": {}}}}),
    )
    msgs = drift_messages(repo, live, surface="chat-rag")
    assert msgs == [
        "chat-rag POST /api/v1/ask: repo has requestBody but live OpenAPI does not",
    ]


def test_drift_messages_ok_when_live_has_body() -> None:
    """Matching requestBody presence yields no drift for that path."""
    body: JsonObject = {
        "content": {"application/json": {"schema": {"type": "object"}}},
    }
    repo = as_json_object(
        cast(
            "object",
            {
                "servers": [{"url": "/api/v1"}],
                "paths": {"/feedback": {"post": {"requestBody": body}}},
            },
        ),
    )
    live = as_json_object(
        cast(
            "object",
            {
                "paths": {"/api/v1/feedback": {"post": {"requestBody": body}}},
            },
        ),
    )
    assert drift_messages(repo, live, surface="chat-rag") == []


def test_required_security_scheme_names_write_and_dm() -> None:
    """Write and DM publish distinct scheme pairs (TC-335)."""
    assert required_security_scheme_names("internal-write") == {
        "bearerAuth",
        "internalApiKey",
    }
    assert required_security_scheme_names("data-management") == {
        "bearerAuth",
        "modalProxyAuth",
    }


def test_drift_messages_flags_missing_security_schemes() -> None:
    """Live must publish declared securitySchemes for write/DM."""
    repo: JsonObject = {"paths": {}, "components": {"securitySchemes": {}}}
    live = as_json_object(
        cast(
            "object",
            {
                "paths": {},
                "components": {"securitySchemes": {"bearerAuth": {"type": "http"}}},
            },
        ),
    )
    msgs = drift_messages(repo, live, surface="internal-write")
    assert "internal-write securitySchemes missing: internalApiKey" in msgs
