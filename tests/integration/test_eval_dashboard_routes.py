"""M64 dashboard API tests (TC-120, TC-122)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests
from vecinita_shared_schemas.json_types import as_json_object

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_list, json_str, response_json_object
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


def test_eval_timeseries_returns_completed_runs(
    eval_write_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """TC-122: timeseries endpoint lists completed runs with metric keys."""
    client, private_key = eval_write_client
    token = sign_test_jwt(private_key, role="admin")
    response = client.get(
        "/internal/v1/eval/runs/timeseries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert "points" in body
    assert "available_metrics" in body
    metrics = body.get("available_metrics")
    assert isinstance(metrics, list)


def test_eval_criteria_crud_admin_only(
    eval_write_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """TC-120: admin can create/list/update criteria; viewer denied."""
    client, private_key = eval_write_client
    admin_token = sign_test_jwt(private_key, role="admin")
    viewer_token = sign_test_jwt(private_key, sub=VIEWER_ID, role="viewer")
    slug = f"tone-friendly-{uuid4().hex[:8]}"

    create = client.post(
        "/internal/v1/eval/criteria",
        json={
            "slug": slug,
            "label": "Friendly tone",
            "rubric": "Answer uses a supportive community tone.",
            "scorer_type": "llm_rubric",
            "enabled": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create.status_code == HTTPStatus.CREATED
    created = response_json_object(create)
    criterion_id = json_str(created, "criterion_id")

    listing = client.get(
        "/internal/v1/eval/criteria",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert listing.status_code == HTTPStatus.OK
    listed = response_json_object(listing)
    items = json_list(listed, "items")
    assert any(json_str(as_json_object(item), "slug") == slug for item in items)

    patch = client.patch(
        f"/internal/v1/eval/criteria/{criterion_id}",
        json={"enabled": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert patch.status_code == HTTPStatus.OK
    patched = response_json_object(patch)
    assert patched.get("enabled") is False

    denied = client.get(
        "/internal/v1/eval/criteria",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert denied.status_code == HTTPStatus.FORBIDDEN
