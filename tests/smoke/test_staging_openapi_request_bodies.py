"""Live staging: ChatRAG OpenAPI must publish ask/feedback request bodies.

[Corpus: staging] [Corpus: api] [Spec: docs/test-plan.md §TC-336]
Env-gated: requires VECINITA_STAGING_CHAT_URL.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import cast

import httpx
import pytest
from vecinita_shared_schemas.json_types import as_json_object

pytestmark = [pytest.mark.live, pytest.mark.smoke]

_CHAT = os.environ.get("VECINITA_STAGING_CHAT_URL", "").rstrip("/")


@pytest.mark.skipif(not _CHAT, reason="VECINITA_STAGING_CHAT_URL unset")
@pytest.mark.parametrize("path", ["/api/v1/ask", "/api/v1/ask/stream", "/api/v1/feedback"])
def test_staging_openapi_post_has_request_body(path: str) -> None:
    """Staging /openapi.json includes requestBody for Request-parsed POSTs."""
    resp = httpx.get(f"{_CHAT}/openapi.json", timeout=30.0)
    assert resp.status_code == HTTPStatus.OK
    openapi = as_json_object(cast("object", resp.json()))
    op = as_json_object(as_json_object(as_json_object(openapi["paths"])[path])["post"])
    assert "requestBody" in op, (
        f"staging {path} missing requestBody — redeploy ChatRAG with "
        "openapi_extra body publishers (TC-332/TC-333)"
    )
