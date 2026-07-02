"""UJ-039 / TC-114: admin triggers eval run via internal-write-api (e2e layer)."""

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


@pytest.fixture
def eval_e2e_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey]]:
    """Write API TestClient + signing key for eval journey."""
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


def test_uj039_admin_triggers_eval_run_and_polls_until_complete(
    eval_e2e_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """UJ-039: admin POST /internal/v1/eval/runs then polls detail until completed."""
    client, private_key = eval_e2e_client
    token = sign_test_jwt(private_key, role="admin")
    create = client.post(
        "/internal/v1/eval/runs",
        json={"corpus_profile": "fixture"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    run_id = UUID(json_str(response_json_object(create), "run_id"))

    detail = None
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
    assert json_str(detail, "status") == "completed"
    items = json_object_list(detail, "items")
    assert items

    summary = json_object_get(detail, "metrics_summary")
    assert summary["faithfulness"] is not None
    assert summary["answer_relevancy"] is not None

    scored_items = [
        item
        for item in items
        if "answer_relevancy" in (metrics := json_object_get(item, "metrics"))
        and metrics["answer_relevancy"] is not None
    ]
    assert scored_items, "TC-112: completed eval must persist answer relevancy per row"

    faithfulness_rows = [
        item
        for item in items
        if "faithfulness" in (metrics := json_object_get(item, "metrics"))
        and metrics["faithfulness"] is not None
    ]
    assert faithfulness_rows, "TC-112: seeded corpus run must persist faithfulness for hit rows"

    history = client.get(
        "/internal/v1/eval/runs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history.status_code == HTTPStatus.OK
    history_body = response_json_object(history)
    history_items = json_object_list(history_body, "items")
    assert any(json_str(item, "run_id") == str(run_id) for item in history_items)
