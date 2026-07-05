"""BUG-2026-07-05: Ollama models list must not 503 when Modal Ollama is unwired (DO maps 503→504 HTML)."""

from __future__ import annotations

import os
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_MODEL_ID

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import (
    find_json_object_by_str,
    json_list,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import auth_headers


@pytest.fixture
def eval_write_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with eval harness dependencies injected."""
    reset_auth_config_for_tests()
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        ),
    )
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-internal-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    return TestClient(
        create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge()),
    )


def test_ollama_models_list_returns_vllm_fallback_when_unconfigured(
    eval_write_client: TestClient,
) -> None:
    """Playground model picker works on vLLM-only deployments (no 503/504 from DO edge)."""
    response = eval_write_client.get(
        "/internal/v1/models/ollama",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    default_model = find_json_object_by_str(
        json_list(body, "items"),
        "model_id",
        DEFAULT_EVAL_MODEL_ID,
    )
    assert default_model.get("available") is True
