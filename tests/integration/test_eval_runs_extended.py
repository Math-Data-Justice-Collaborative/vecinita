"""EV-009 F37 — extended POST /eval/runs with config snapshot (TC-128 partial, T68.6)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.helpers.json_response import json_object_get, json_str, response_json_object
from tests.unit.rag.conftest import seed_eval_corpus
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

_CUSTOM_TOP_K = 9
_PRESET_TOP_K = 7
_OVERRIDE_TOP_K = 11


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def extended_eval_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey, list[UUID], list[UUID]]]:
    """Authenticated client; tracks preset and run ids for cleanup."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    database_url = _database_url()
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    seed_eval_corpus(database_url=database_url)
    app = create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge())
    preset_ids: list[UUID] = []
    run_ids: list[UUID] = []
    engine = create_engine(database_url)
    with TestClient(app) as client:
        yield client, private_key, preset_ids, run_ids
    with engine.begin() as conn:
        for run_id in run_ids:
            conn.execute(
                text("DELETE FROM eval_run_items WHERE run_id = :id"),
                {"id": run_id},
            )
            conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})
        for preset_id in preset_ids:
            conn.execute(
                text("DELETE FROM eval_config_presets WHERE id = :id"),
                {"id": preset_id},
            )
    reset_auth_config_for_tests()


def _admin_token(private_key: EllipticCurvePrivateKey, *, sub: UUID | None = None) -> str:
    return sign_test_jwt(private_key, sub=sub or uuid4(), role="admin")


def _create_preset(
    client: TestClient,
    token: str,
    preset_ids: list[UUID],
    *,
    shared: bool = False,
) -> UUID:
    response = client.post(
        "/internal/v1/eval/config-presets",
        json={
            "name": "run-preset",
            "config": {
                "top_k": _PRESET_TOP_K,
                "system_prompt": "Preset sandbox prompt for eval runs.",
            },
            "shared": shared,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.CREATED
    body = response_json_object(response)
    preset_id = UUID(json_str(body, "preset_id"))
    preset_ids.append(preset_id)
    return preset_id


def test_create_eval_run_persists_config_snapshot(
    extended_eval_client: tuple[TestClient, EllipticCurvePrivateKey, list[UUID], list[UUID]],
) -> None:
    """TC-128 (API): POST with config overrides persists config_snapshot on the run."""
    client, private_key, _preset_ids, run_ids = extended_eval_client
    token = _admin_token(private_key)
    with patch("vecinita_internal_write_api.app.execute_eval_run"):
        response = client.post(
            "/internal/v1/eval/runs",
            json={
                "mode": "golden",
                "config": {
                    "top_k": _CUSTOM_TOP_K,
                    "system_prompt": "Custom sandbox prompt for golden eval.",
                },
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == HTTPStatus.ACCEPTED
    created = response_json_object(response)
    run_id = UUID(json_str(created, "run_id"))
    run_ids.append(run_id)

    detail = client.get(
        f"/internal/v1/eval/runs/{run_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == HTTPStatus.OK
    detail_body = response_json_object(detail)
    assert json_str(detail_body, "mode") == "golden"
    snapshot = json_object_get(detail_body, "config_snapshot")
    assert snapshot.get("top_k") == _CUSTOM_TOP_K
    assert snapshot.get("system_prompt") == "Custom sandbox prompt for golden eval."


def test_create_eval_run_merges_preset_and_request_config(
    extended_eval_client: tuple[TestClient, EllipticCurvePrivateKey, list[UUID], list[UUID]],
) -> None:
    """POST with preset_id merges preset config then applies request overrides."""
    client, private_key, preset_ids, run_ids = extended_eval_client
    owner_id = uuid4()
    token = _admin_token(private_key, sub=owner_id)
    preset_id = _create_preset(client, token, preset_ids, shared=True)

    with patch("vecinita_internal_write_api.app.execute_eval_run"):
        response = client.post(
            "/internal/v1/eval/runs",
            json={
                "preset_id": str(preset_id),
                "config": {"top_k": _OVERRIDE_TOP_K},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == HTTPStatus.ACCEPTED
    run_id = UUID(json_str(response_json_object(response), "run_id"))
    run_ids.append(run_id)

    detail = client.get(
        f"/internal/v1/eval/runs/{run_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    detail_body = response_json_object(detail)
    snapshot = json_object_get(detail_body, "config_snapshot")
    assert snapshot.get("top_k") == _OVERRIDE_TOP_K
    assert snapshot.get("system_prompt") == "Preset sandbox prompt for eval runs."
    assert json_str(detail_body, "preset_id") == str(preset_id)


def test_create_eval_run_adhoc_requires_question(
    extended_eval_client: tuple[TestClient, EllipticCurvePrivateKey, list[UUID], list[UUID]],
) -> None:
    """POST with mode=adhoc and no question returns 422."""
    client, private_key, _preset_ids, _run_ids = extended_eval_client
    token = _admin_token(private_key)
    response = client.post(
        "/internal/v1/eval/runs",
        json={"mode": "adhoc"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_eval_run_unknown_preset_returns_404(
    extended_eval_client: tuple[TestClient, EllipticCurvePrivateKey, list[UUID], list[UUID]],
) -> None:
    """POST with unknown preset_id returns 404."""
    client, private_key, _preset_ids, _run_ids = extended_eval_client
    token = _admin_token(private_key)
    with patch("vecinita_internal_write_api.app.execute_eval_run"):
        response = client.post(
            "/internal/v1/eval/runs",
            json={"preset_id": str(uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_eval_run_private_preset_from_other_admin_returns_403(
    extended_eval_client: tuple[TestClient, EllipticCurvePrivateKey, list[UUID], list[UUID]],
) -> None:
    """POST referencing another admin's private preset returns 403."""
    client, private_key, preset_ids, _run_ids = extended_eval_client
    owner_token = _admin_token(private_key, sub=uuid4())
    other_token = _admin_token(private_key, sub=uuid4())
    preset_id = _create_preset(client, owner_token, preset_ids, shared=False)

    response = client.post(
        "/internal/v1/eval/runs",
        json={"preset_id": str(preset_id)},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
