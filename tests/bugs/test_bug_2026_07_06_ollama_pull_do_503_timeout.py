"""BUG-2026-07-06: Ollama pull 503 — DO wraps upstream JSON 503 as HTML error page.

Production symptom: POST /internal/v1/models/ollama/pull returns DO HTML 503/504
(`via_upstream`, `connection_timed_out`) in ~200ms — not a slow gateway timeout.

Root cause: internal-write-api returns JSON 503 when Modal Ollama is unwired; DO App
Platform replaces upstream 503 with its HTML error page. GET list still returns 200
(vLLM fallback + catalog) so the Download UI is shown for unavailable models.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_list, response_json_object
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)


@pytest.fixture
def super_admin_write_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, dict[str, str]]:
    """Super-admin TestClient with eval harness; Modal Ollama env vars unset."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        ),
    )
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_OLLAMA_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    set_auth_config_for_tests(make_auth_config(private_key))
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(
        create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge()),
    )
    headers = {"Authorization": f"Bearer {sign_test_jwt(private_key, role='super-admin')}"}
    return client, headers


def test_ollama_pull_unconfigured_returns_json_503_detail(
    super_admin_write_client: tuple[TestClient, dict[str, str]],
) -> None:
    """Upstream JSON 503 (fast) — DO maps this to HTML connection_timed_out in production."""
    client, headers = super_admin_write_client
    response = client.post(
        "/internal/v1/models/ollama/pull",
        json={"model_id": "qwen2.5:0.5b-instruct"},
        headers=headers,
    )
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    body = response_json_object(response)
    detail = body.get("detail")
    assert isinstance(detail, str)
    assert "not configured" in detail.lower()


def test_ollama_list_still_ok_while_pull_unconfigured(
    super_admin_write_client: tuple[TestClient, dict[str, str]],
) -> None:
    """List fallback masks missing Ollama wiring — Download UI can still be shown."""
    client, headers = super_admin_write_client
    response = client.get("/internal/v1/models/ollama", headers=headers)
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    items = json_list(body, "items")
    assert len(items) >= 1


def test_ollama_pull_returns_202_when_client_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After wiring Modal Ollama, pull must return 202 (not DO HTML 503)."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        ),
    )
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    from tests.helpers.ollama_models_mock import MockOllamaModelsClient  # noqa: PLC0415

    client = TestClient(
        create_app(
            eval_embed_fn=eval_embed_fn,
            eval_judge=MockEvalJudge(),
            ollama_models_client=MockOllamaModelsClient(),
        ),
    )
    headers = {"Authorization": f"Bearer {sign_test_jwt(private_key, role='super-admin')}"}
    response = client.post(
        "/internal/v1/models/ollama/pull",
        json={"model_id": "qwen2.5:0.5b-instruct"},
        headers=headers,
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    assert body.get("status") == "pulling"
    assert body.get("model_id") == "qwen2.5:0.5b-instruct"
    assert isinstance(body.get("job_id"), str)


def test_infra_do_spec_declares_modal_llm_url() -> None:
    """Repo spec includes LLM URL — live DO drift is the production failure mode."""
    spec_path = Path(__file__).resolve().parents[2] / "infra" / "do" / "internal-write-api.yaml"
    content = spec_path.read_text(encoding="utf-8")
    assert "VECINITA_MODAL_LLM_URL" in content
