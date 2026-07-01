"""Unit tests for eval HTTP routes on internal write API (F36, ADR-034)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_int, json_str, response_json_object
from tests.unit.internal_write_api.conftest import auth_headers, database_url
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine


@pytest.fixture
def eval_write_client(internal_api_env: None) -> TestClient:
    """TestClient with eval harness dependencies injected."""
    _ = internal_api_env
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    return TestClient(
        create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge()),
    )


def test_create_eval_run_route_accepts_empty_body(eval_write_client: TestClient) -> None:
    """POST /eval/runs defaults corpus_profile and schedules background execution."""
    with patch("vecinita_internal_write_api.app.execute_eval_run"):
        response = eval_write_client.post(
            "/internal/v1/eval/runs",
            headers=auth_headers(),
        )
    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    assert json_str(body, "status") == "pending"


def test_list_eval_runs_clamps_pagination(eval_write_client: TestClient) -> None:
    """GET /eval/runs clamps page and page_size to supported bounds."""
    response = eval_write_client.get(
        "/internal/v1/eval/runs",
        params={"page": 0, "page_size": 500},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_int(body, "page") == 1
    assert json_int(body, "page_size") == 100


def test_get_eval_timeseries_clamps_limit(eval_write_client: TestClient) -> None:
    """GET /eval/runs/timeseries clamps limit between 1 and 500."""
    low = eval_write_client.get(
        "/internal/v1/eval/runs/timeseries",
        params={"limit": 0},
        headers=auth_headers(),
    )
    high = eval_write_client.get(
        "/internal/v1/eval/runs/timeseries",
        params={"limit": 999},
        headers=auth_headers(),
    )
    assert low.status_code == HTTPStatus.OK
    assert high.status_code == HTTPStatus.OK


def test_get_eval_run_route_returns_404(eval_write_client: TestClient) -> None:
    """GET /eval/runs/{id} returns 404 for unknown ids."""
    response = eval_write_client.get(
        f"/internal/v1/eval/runs/{uuid4()}",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_eval_criteria_crud_and_patch_404(eval_write_client: TestClient) -> None:
    """Criteria list/create succeed; PATCH unknown id returns 404."""
    slug = f"unit-criterion-{uuid4().hex[:8]}"
    create = eval_write_client.post(
        "/internal/v1/eval/criteria",
        json={
            "slug": slug,
            "label": "Unit criterion",
            "rubric": "Score the answer.",
            "scorer_type": "llm_rubric",
            "enabled": True,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.CREATED
    criterion_id = json_str(response_json_object(create), "criterion_id")

    listing = eval_write_client.get(
        "/internal/v1/eval/criteria",
        headers=auth_headers(),
    )
    assert listing.status_code == HTTPStatus.OK

    patch = eval_write_client.patch(
        f"/internal/v1/eval/criteria/{criterion_id}",
        json={"enabled": False},
        headers=auth_headers(),
    )
    assert patch.status_code == HTTPStatus.OK

    missing = eval_write_client.patch(
        f"/internal/v1/eval/criteria/{uuid4()}",
        json={"enabled": True},
        headers=auth_headers(),
    )
    assert missing.status_code == HTTPStatus.NOT_FOUND


def test_get_eval_run_route_returns_detail(
    engine: Engine,
    eval_write_client: TestClient,
) -> None:
    """GET /eval/runs/{id} returns persisted run detail."""
    from sqlalchemy import text
    from vecinita_internal_write_api.eval_service import create_eval_run

    created = create_eval_run(engine, corpus_profile="fixture")
    try:
        response = eval_write_client.get(
            f"/internal/v1/eval/runs/{created.run_id}",
            headers=auth_headers(),
        )
        assert response.status_code == HTTPStatus.OK
        body = response_json_object(response)
        assert json_str(body, "status") == "pending"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": created.run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": created.run_id})


def test_ingest_audit_event_rejects_operator_jwt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /audit/event rejects operator JWTs (service key only)."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-internal-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key, internal_api_key="test-internal-key"))

    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415
    from tests.unit.shared_schemas.auth_fixtures import sign_test_jwt

    client = TestClient(create_app())
    token = sign_test_jwt(private_key, role="admin")
    try:
        response = client.post(
            "/internal/v1/audit/event",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "event_type": "user.invited",
                "entity_type": "user",
                "entity_id": str(uuid4()),
                "payload": {},
            },
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
    finally:
        reset_auth_config_for_tests()


def test_ingest_audit_event_service_key(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /audit/event accepts the internal service key and returns 202."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-internal-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key, internal_api_key="test-internal-key"))

    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    client = TestClient(create_app())
    entity_id = uuid4()
    try:
        response = client.post(
            "/internal/v1/audit/event",
            headers=auth_headers(),
            json={
                "event_type": "user.invited",
                "entity_type": "user",
                "entity_id": str(entity_id),
                "payload": {"role": "viewer"},
            },
        )
        assert response.status_code == HTTPStatus.ACCEPTED
    finally:
        reset_auth_config_for_tests()
        with engine.begin() as conn:
            from sqlalchemy import text

            conn.execute(
                text("DELETE FROM audit_log WHERE entity_id = :id"),
                {"id": entity_id},
            )
