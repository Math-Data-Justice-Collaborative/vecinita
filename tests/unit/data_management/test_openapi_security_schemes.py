"""TC-335b: Data Management OpenAPI publishes bearer + proxy security schemes."""

from __future__ import annotations

from typing import cast

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_shared_schemas.json_types import as_json_object

pytestmark = pytest.mark.unit


def test_dm_openapi_publishes_bearer_and_proxy_schemes() -> None:
    """Live DM /openapi.json documents bearerAuth + modalProxyAuth."""
    openapi = as_json_object(
        cast("object", TestClient(create_app(require_proxy_auth=False)).get("/openapi.json").json())
    )
    schemes = as_json_object(as_json_object(openapi["components"])["securitySchemes"])
    bearer = as_json_object(schemes["bearerAuth"])
    assert bearer["type"] == "http"
    assert bearer["scheme"] == "bearer"
    proxy = as_json_object(schemes["modalProxyAuth"])
    assert proxy["type"] == "apiKey"
    assert proxy["name"] == "X-Vecinita-Proxy-Key"
