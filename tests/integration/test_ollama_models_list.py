"""EV-009/EV-010 F37/F38 — Modal Ollama model list + pull (TC-134, UJ-045, UJ-048)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import (
    find_json_object_by_str,
    json_list,
    json_str,
    response_json_object,
)
from tests.helpers.ollama_models_mock import MockOllamaModelsClient
from tests.helpers.user_mgmt_e2e import VIEWER_ID
from tests.unit.rag.conftest import seed_eval_corpus
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def ollama_models_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient]]:
    """Authenticated internal-write client with mocked Modal Ollama backend."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    database_url = _database_url()
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    seed_eval_corpus(database_url=database_url)
    mock_client = MockOllamaModelsClient()
    app = create_app(
        eval_embed_fn=eval_embed_fn,
        eval_judge=MockEvalJudge(),
        ollama_models_client=mock_client,
    )
    with TestClient(app) as client:
        yield client, private_key, mock_client
    reset_auth_config_for_tests()


def test_admin_lists_ollama_models(
    ollama_models_client: tuple[TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient],
) -> None:
    """TC-134: admin lists Ollama models for the Playground picker."""
    client, private_key, _mock_client = ollama_models_client
    token = sign_test_jwt(private_key, role="admin")

    listing = client.get(
        "/internal/v1/models/ollama",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listing.status_code == HTTPStatus.OK
    listing_body = response_json_object(listing)
    default_model = find_json_object_by_str(
        json_list(listing_body, "items"),
        "model_id",
        "qwen2.5:1.5b-instruct",
    )
    assert default_model.get("available") is True


def test_admin_cannot_trigger_ollama_pull(
    ollama_models_client: tuple[TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient],
) -> None:
    """TC-134 / F38: admin receives 403 on pull — super-admin only (RD-147)."""
    client, private_key, mock_client = ollama_models_client
    token = sign_test_jwt(private_key, role="admin")

    pull = client.post(
        "/internal/v1/models/ollama/pull",
        json={"model_id": "llama3.2:3b"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pull.status_code == HTTPStatus.FORBIDDEN
    assert mock_client.pull_requests == []


def test_super_admin_triggers_ollama_pull(
    ollama_models_client: tuple[TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient],
) -> None:
    """TC-134 / F38: super-admin can start a background Ollama pull (UJ-048)."""
    client, private_key, mock_client = ollama_models_client
    token = sign_test_jwt(private_key, role="super-admin")

    pull = client.post(
        "/internal/v1/models/ollama/pull",
        json={"model_id": "llama3.2:3b"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pull.status_code == HTTPStatus.ACCEPTED
    pull_body = response_json_object(pull)
    assert json_str(pull_body, "model_id") == "llama3.2:3b"
    assert pull_body.get("status") == "pulling"
    assert pull_body.get("job_id") is not None
    assert mock_client.pull_requests == ["llama3.2:3b"]


def test_viewer_denied_on_ollama_model_routes(
    ollama_models_client: tuple[TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient],
) -> None:
    """TC-134: viewer JWT receives 403 on Ollama model endpoints."""
    client, private_key, _mock_client = ollama_models_client
    token = sign_test_jwt(private_key, sub=VIEWER_ID, role="viewer")

    assert (
        client.get(
            "/internal/v1/models/ollama",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        client.post(
            "/internal/v1/models/ollama/pull",
            json={"model_id": "llama3.2:3b"},
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
