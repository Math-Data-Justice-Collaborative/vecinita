"""UJ-045 / TC-128-TC-129: playground eval runs via internal-write-api (e2e layer)."""

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
from tests.helpers.json_response import (
    json_object_get,
    json_object_list,
    json_str,
    response_json_object,
)
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

_SANDBOX_TOP_K = 11
_SANDBOX_PROMPT = "Sandbox-only system prompt for UJ-045 golden eval."
_ADHOC_QUESTION = "What are the community food pantry hours this week?"


@pytest.fixture
def playground_eval_e2e_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey]]:
    """Write API TestClient + signing key for playground eval journeys."""
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


def _poll_eval_run_detail(
    client: TestClient,
    token: str,
    run_id: UUID,
) -> dict[str, object]:
    detail: dict[str, object] | None = None
    for _ in range(40):
        response = client.get(
            f"/internal/v1/eval/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == HTTPStatus.OK
        detail = response_json_object(response)
        if json_str(detail, "status") in {"completed", "failed"}:
            break
        time.sleep(0.1)
    assert detail is not None
    return detail


def test_uj045_golden_playground_run_persists_config_snapshot(
    playground_eval_e2e_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """TC-128: golden batch with config overrides persists config_snapshot on the run."""
    client, private_key = playground_eval_e2e_client
    token = sign_test_jwt(private_key, role="admin")
    create = client.post(
        "/internal/v1/eval/runs",
        json={
            "mode": "golden",
            "config": {
                "top_k": _SANDBOX_TOP_K,
                "system_prompt": _SANDBOX_PROMPT,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    run_id = UUID(json_str(response_json_object(create), "run_id"))

    detail = _poll_eval_run_detail(client, token, run_id)
    assert json_str(detail, "status") == "completed"
    assert json_str(detail, "mode") == "golden"
    snapshot = json_object_get(detail, "config_snapshot")
    assert snapshot.get("top_k") == _SANDBOX_TOP_K
    assert snapshot.get("system_prompt") == _SANDBOX_PROMPT
    items = json_object_list(detail, "items")
    assert items


def test_uj045_adhoc_playground_run_persists_question(
    playground_eval_e2e_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """TC-129: ad-hoc mode runs one question and persists it on eval_run_items."""
    client, private_key = playground_eval_e2e_client
    token = sign_test_jwt(private_key, role="admin")
    create = client.post(
        "/internal/v1/eval/runs",
        json={
            "mode": "adhoc",
            "question": _ADHOC_QUESTION,
            "config": {
                "top_k": _SANDBOX_TOP_K,
                "system_prompt": _SANDBOX_PROMPT,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    run_id = UUID(json_str(response_json_object(create), "run_id"))

    detail = _poll_eval_run_detail(client, token, run_id)
    assert json_str(detail, "status") == "completed"
    assert json_str(detail, "mode") == "adhoc"
    items = json_object_list(detail, "items")
    assert len(items) == 1
    row = items[0]
    assert json_str(row, "case_id") == "adhoc"
    assert json_str(row, "question") == _ADHOC_QUESTION
    metrics = json_object_get(row, "metrics")
    assert metrics.get("latency_ms") is not None
