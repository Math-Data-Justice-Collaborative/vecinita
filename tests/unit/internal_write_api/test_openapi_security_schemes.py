"""TC-335: Internal write OpenAPI publishes bearer security schemes.

[Corpus: api] [Spec: docs/test-plan.md §TC-335]
[Spec: docs/adr/ADR-011-openapi-contract-source-of-truth.md]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_openapi_publishes_bearer_and_internal_api_key_schemes(
    write_client: TestClient,
) -> None:
    """Live /openapi.json documents bearerAuth + internalApiKey (HTTP bearer)."""
    openapi = as_json_object(cast("object", write_client.get("/openapi.json").json()))
    components = as_json_object(openapi["components"])
    schemes = as_json_object(components["securitySchemes"])
    bearer = as_json_object(schemes["bearerAuth"])
    assert bearer["type"] == "http"
    assert bearer["scheme"] == "bearer"
    internal = as_json_object(schemes["internalApiKey"])
    assert internal["type"] == "http"
    assert internal["scheme"] == "bearer"
