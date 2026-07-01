"""EV-008 F36 — internal-write-api eval routes (TC-114, TC-115)."""

from __future__ import annotations

import os
import time
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_object_get, json_str, response_json_object
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


@pytest.fixture
def eval_write_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey]]:
    """Authenticated internal-write client with eval dependencies injected."""
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
    app = create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge())
    with TestClient(app) as client:
        yield client, private_key
    reset_auth_config_for_tests()


def _poll_run(
    client: TestClient, token: str, run_id: UUID, *, attempts: int = 30
) -> dict[str, object]:
    for _ in range(attempts):
        response = client.get(
            f"/internal/v1/eval/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == HTTPStatus.OK
        body = response_json_object(response)
        status = json_str(body, "status")
        if status in {"completed", "failed"}:
            return body
        time.sleep(0.1)
    msg = f"eval run {run_id} did not complete"
    raise AssertionError(msg)


def test_admin_triggers_eval_run_and_persists_results(
    eval_write_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """TC-114: admin POST creates a run that completes with summary metrics."""
    client, private_key = eval_write_client
    token = sign_test_jwt(private_key, role="admin")
    response = client.post(
        "/internal/v1/eval/runs",
        json={"corpus_profile": "fixture"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    created = response_json_object(response)
    run_id = UUID(json_str(created, "run_id"))
    detail_obj = _poll_run(client, token, run_id)
    assert json_str(detail_obj, "status") == "completed"
    summary = json_object_get(detail_obj, "metrics_summary")
    assert summary.get("retrieval_relevance") is not None


def test_viewer_read_only_eval_routes(
    eval_write_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """TC-115: viewer JWT can GET eval dashboards but receives 403 on POST."""
    client, private_key = eval_write_client
    token = sign_test_jwt(private_key, sub=VIEWER_ID, role="viewer")
    post = client.post(
        "/internal/v1/eval/runs",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert post.status_code == HTTPStatus.FORBIDDEN
    listing = client.get(
        "/internal/v1/eval/runs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listing.status_code == HTTPStatus.OK
