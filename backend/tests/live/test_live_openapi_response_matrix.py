"""Deterministic live checks for documented non-2xx OpenAPI responses.

These complement Schemathesis POSITIVE fuzzing: each test issues a single
crafted request and asserts status plus minimal body shape (no Hypothesis).

Requires ``RENDER_AGENT_URL`` and/or ``RENDER_GATEWAY_URL`` depending on the
case (fixtures skip when the URL is unset).
"""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def _detail_is_fastapi_validation(body: object) -> bool:
    assert isinstance(body, dict), f"expected JSON object, got {type(body)}"
    detail = body.get("detail")
    if isinstance(detail, list):
        return True
    if isinstance(detail, str):
        return True
    return False


def test_agent_ask_rerank_top_k_out_of_range_422(live_direct_agent_url: str) -> None:
    resp = requests.get(
        f"{live_direct_agent_url}/ask",
        params={"question": "x", "rerank": "true", "rerank_top_k": "0"},
        timeout=30,
    )
    assert resp.status_code == 422, resp.text
    assert _detail_is_fastapi_validation(resp.json()), (
        "expected FastAPI validation error body with str or list detail"
    )


def test_agent_ask_missing_question_returns_400(live_direct_agent_url: str) -> None:
    resp = requests.get(f"{live_direct_agent_url}/ask", timeout=20)
    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert "detail" in body


def test_gateway_ask_missing_required_question_422(gateway_url: str) -> None:
    resp = requests.get(f"{gateway_url}/api/v1/ask", timeout=20)
    assert resp.status_code == 422, resp.text
    assert _detail_is_fastapi_validation(resp.json()), (
        "expected FastAPI validation error body with str or list detail"
    )


def test_gateway_ask_invalid_rerank_top_k_422(gateway_url: str) -> None:
    resp = requests.get(
        f"{gateway_url}/api/v1/ask",
        params={"question": "housing resources", "rerank": "true", "rerank_top_k": "99"},
        timeout=30,
    )
    assert resp.status_code == 422, resp.text
    assert _detail_is_fastapi_validation(resp.json()), (
        "expected FastAPI validation error body with str or list detail"
    )
