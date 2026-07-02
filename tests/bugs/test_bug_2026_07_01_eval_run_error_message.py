"""BUG-2026-07-01: failed eval runs must expose error_message in GET detail."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.app import create_app
from vecinita_internal_write_api.eval_service import execute_eval_run
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_runs import create_test_eval_run
from tests.helpers.json_response import json_str, response_json_object
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.unit

_EMBED_404_MESSAGE = "embed failed with status 404: modal-http: invalid function call"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    """SQLAlchemy engine for eval run persistence tests."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(generate_es256_keypair()))
    eng = create_engine(_database_url())
    yield eng
    eng.dispose()


@pytest.fixture
def eval_bug_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey]]:
    """Write API TestClient with admin JWT for eval routes."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    client = TestClient(create_app())
    yield client, private_key
    reset_auth_config_for_tests()


def test_get_eval_run_detail_includes_error_message_when_failed(
    engine: Engine,
    eval_bug_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """GET /eval/runs/{id} returns stored error_message for failed runs."""
    client, private_key = eval_bug_client
    created = create_test_eval_run(engine, corpus_profile="fixture")
    run_id = created.response.run_id
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE eval_runs
                    SET status = 'failed',
                        completed_at = now(),
                        error_message = :error
                    WHERE id = :id
                    """
                ),
                {"id": run_id, "error": _EMBED_404_MESSAGE},
            )

        token = sign_test_jwt(private_key, role="admin")
        response = client.get(
            f"/internal/v1/eval/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == HTTPStatus.OK
        body = response_json_object(response)
        assert json_str(body, "status") == "failed"
        assert json_str(body, "error_message") == _EMBED_404_MESSAGE
        assert body.get("items") == []
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})


def test_execute_eval_run_persists_embed_client_error_for_api(
    engine: Engine,
    eval_bug_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """Background eval failure from embed 404 is readable via GET detail error_message."""
    client, private_key = eval_bug_client
    created = create_test_eval_run(engine, corpus_profile="fixture")
    run_id = created.response.run_id
    try:
        with (
            patch(
                "vecinita_internal_write_api.eval_service.run_golden_eval",
                side_effect=RuntimeError(_EMBED_404_MESSAGE),
            ),
            pytest.raises(RuntimeError, match="invalid function call"),
        ):
            execute_eval_run(
                engine,
                run_id=run_id,
                embed_fn=eval_embed_fn,
            )

        token = sign_test_jwt(private_key, role="admin")
        response = client.get(
            f"/internal/v1/eval/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == HTTPStatus.OK
        body = response_json_object(response)
        assert json_str(body, "status") == "failed"
        assert json_str(body, "error_message") == _EMBED_404_MESSAGE
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})


def test_get_eval_run_detail_error_message_null_when_completed(
    engine: Engine,
    eval_bug_client: tuple[TestClient, EllipticCurvePrivateKey],
) -> None:
    """Completed runs omit error_message (null)."""
    client, private_key = eval_bug_client
    created = create_test_eval_run(engine, corpus_profile="fixture")
    run_id = created.response.run_id
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE eval_runs
                    SET status = 'completed',
                        completed_at = now(),
                        metrics_summary = '{"retrieval_relevance": 0.9}'::jsonb
                    WHERE id = :id
                    """
                ),
                {"id": run_id},
            )

        token = sign_test_jwt(private_key, role="admin")
        response = client.get(
            f"/internal/v1/eval/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = response_json_object(response)
        assert json_str(body, "status") == "completed"
        assert body.get("error_message") is None
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})
