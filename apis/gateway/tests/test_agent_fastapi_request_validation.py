"""FastAPI + Pydantic validation tests for the agent app (422 contracts, OpenAPI examples).

Best practices exercised:
  * Request bodies validated before route handlers (``ModelSelection`` Field constraints).
  * Query enums / literals rejected with 422 when not in the declared type (``tag_match_mode``).
  * OpenAPI documents ``openapi_examples`` for Schemathesis / Swagger explicit cases.
"""

import pytest

pytestmark = pytest.mark.unit


def test_post_model_selection_empty_provider_returns_422(fastapi_client):
    response = fastapi_client.post("/model-selection", json={"provider": "", "model": None})
    assert response.status_code == 422
    body = response.json()
    assert body.get("detail")


def test_post_model_selection_missing_provider_returns_422(fastapi_client):
    response = fastapi_client.post("/model-selection", json={"model": "gemma3"})
    assert response.status_code == 422


def test_post_model_selection_model_exceeds_max_length_returns_422(fastapi_client):
    response = fastapi_client.post(
        "/model-selection",
        json={"provider": "ollama", "model": "x" * 201, "lock": False},
    )
    assert response.status_code == 422


def test_get_ask_invalid_tag_match_mode_returns_422(fastapi_client):
    response = fastapi_client.get(
        "/ask",
        params={
            "question": "What is a food bank?",
            "tag_match_mode": "invalid_mode",
        },
    )
    assert response.status_code == 422


def test_get_ask_stream_invalid_tag_match_mode_returns_422(fastapi_client):
    response = fastapi_client.get(
        "/ask/stream",
        params={
            "question": "What is a food bank?",
            "tag_match_mode": "neither",
        },
    )
    assert response.status_code == 422


def test_openapi_includes_parameter_examples_for_ask(fastapi_client):
    """Regression: explicit examples help Schemathesis and humans; see ``openapi_examples``."""
    r = fastapi_client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    ask_get = spec.get("paths", {}).get("/ask", {}).get("get", {})
    params = ask_get.get("parameters") or []
    by_name = {p["name"]: p for p in params if p.get("in") == "query"}
    assert "question" in by_name
    # FastAPI 0.115+ maps openapi_examples to OAS parameter.examples
    q_param = by_name["question"]
    assert (
        "examples" in q_param or "example" in q_param
    ), f"expected examples on question param, got keys: {sorted(q_param.keys())}"


def test_openapi_post_model_selection_documents_403_for_lock_policy(fastapi_client):
    """Schemathesis should not treat 403 as generic missing-auth when selection is locked."""
    r = fastapi_client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    post = spec["paths"]["/model-selection"]["post"]
    assert "403" in post["responses"]
    desc = (post["responses"]["403"].get("description") or "").lower()
    assert "locked" in desc or "policy" in desc or "missing-bearer" in desc
