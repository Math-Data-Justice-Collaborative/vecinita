"""UJ-048 / TC-138: super-admin playground model download (API e2e layer)."""

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
from tests.unit.rag.conftest import seed_eval_corpus
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_DOWNLOAD_MODEL_ID = "qwen2.5:3b-instruct"


@pytest.fixture
def playground_download_e2e_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient]]:
    """Write API TestClient with mocked Modal Ollama backend."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
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


def test_uj048_super_admin_pull_then_list_includes_model(
    playground_download_e2e_client: tuple[
        TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient
    ],
) -> None:
    """TC-138: super-admin POST pull returns 202; list includes pulling model."""
    client, private_key, mock_client = playground_download_e2e_client
    super_token = sign_test_jwt(private_key, role="super-admin")

    pull = client.post(
        "/internal/v1/models/ollama/pull",
        json={"model_id": _DOWNLOAD_MODEL_ID},
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert pull.status_code == HTTPStatus.ACCEPTED
    pull_body = response_json_object(pull)
    assert json_str(pull_body, "model_id") == _DOWNLOAD_MODEL_ID
    assert pull_body.get("status") == "pulling"
    assert mock_client.pull_requests == [_DOWNLOAD_MODEL_ID]

    listing = client.get(
        "/internal/v1/models/ollama",
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert listing.status_code == HTTPStatus.OK
    entry = find_json_object_by_str(
        json_list(response_json_object(listing), "items"),
        "model_id",
        _DOWNLOAD_MODEL_ID,
    )
    assert entry.get("available") is False


def test_uj048_admin_pull_forbidden(
    playground_download_e2e_client: tuple[
        TestClient, EllipticCurvePrivateKey, MockOllamaModelsClient
    ],
) -> None:
    """TC-138 / AC-E28: admin JWT cannot trigger model pull."""
    client, private_key, mock_client = playground_download_e2e_client
    admin_token = sign_test_jwt(private_key, role="admin")

    pull = client.post(
        "/internal/v1/models/ollama/pull",
        json={"model_id": _DOWNLOAD_MODEL_ID},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pull.status_code == HTTPStatus.FORBIDDEN
    assert mock_client.pull_requests == []
