"""EV-009 F37 — eval config preset CRUD (TC-127, UJ-045)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
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


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def preset_write_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey, list[UUID]]]:
    """Authenticated internal-write client for preset integration tests."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    database_url = _database_url()
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    seed_eval_corpus(database_url=database_url)
    app = create_app(eval_embed_fn=eval_embed_fn, eval_judge=MockEvalJudge())
    created_ids: list[UUID] = []
    engine = create_engine(database_url)
    with TestClient(app) as client:
        yield client, private_key, created_ids
    with engine.begin() as conn:
        for preset_id in created_ids:
            conn.execute(
                text("DELETE FROM eval_config_presets WHERE id = :id"),
                {"id": preset_id},
            )
    reset_auth_config_for_tests()


def _track_preset(created_ids: list[UUID], body: dict[str, object]) -> UUID:
    preset_id = UUID(json_str(body, "preset_id"))
    created_ids.append(preset_id)
    return preset_id


_CUSTOM_TOP_K = 7
_EXPECTED_VERSION_AFTER_PATCH = 2


def test_owner_crud_and_shared_clone(
    preset_write_client: tuple[TestClient, EllipticCurvePrivateKey, list[UUID]],
) -> None:
    """TC-127: owner CRUD; other admin reads shared preset and clones."""
    client, private_key, created_ids = preset_write_client
    owner_id = uuid4()
    other_admin_id = uuid4()
    owner_token = sign_test_jwt(private_key, sub=owner_id, role="admin")
    other_token = sign_test_jwt(private_key, sub=other_admin_id, role="admin")

    create = client.post(
        "/internal/v1/eval/config-presets",
        json={
            "name": "baseline",
            "config": {"top_k": _CUSTOM_TOP_K, "system_prompt": "Sandbox rules for eval."},
            "shared": True,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create.status_code == HTTPStatus.CREATED
    created = response_json_object(create)
    preset_id = _track_preset(created_ids, created)
    assert json_str(created, "name") == "baseline"
    assert json_object_get(created, "config").get("top_k") == _CUSTOM_TOP_K

    listing = client.get(
        "/internal/v1/eval/config-presets",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert listing.status_code == HTTPStatus.OK
    listing_body = response_json_object(listing)
    items_raw = listing_body.get("items")
    assert isinstance(items_raw, list)
    assert any(
        isinstance(item, dict) and json_str(item, "preset_id") == str(preset_id)
        for item in items_raw
    )

    patch = client.patch(
        f"/internal/v1/eval/config-presets/{preset_id}",
        json={"name": "baseline-v2"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert patch.status_code == HTTPStatus.OK
    patched = response_json_object(patch)
    assert json_str(patched, "name") == "baseline-v2"
    assert int(str(patched.get("version"))) == _EXPECTED_VERSION_AFTER_PATCH

    forbidden_patch = client.patch(
        f"/internal/v1/eval/config-presets/{preset_id}",
        json={"shared": False},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_patch.status_code == HTTPStatus.FORBIDDEN

    clone = client.post(
        f"/internal/v1/eval/config-presets/{preset_id}/clone",
        json={"name": "my-copy"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert clone.status_code == HTTPStatus.CREATED
    cloned = response_json_object(clone)
    clone_id = _track_preset(created_ids, cloned)
    assert json_str(cloned, "name") == "my-copy"
    assert cloned.get("shared") is False
    assert json_str(cloned, "owner_id") == str(other_admin_id)
    assert clone_id != preset_id


def test_viewer_denied_on_preset_routes(
    preset_write_client: tuple[TestClient, EllipticCurvePrivateKey, list[UUID]],
) -> None:
    """TC-127: viewer JWT receives 403 on preset endpoints."""
    client, private_key, _created_ids = preset_write_client
    token = sign_test_jwt(private_key, sub=VIEWER_ID, role="viewer")
    preset_id = uuid4()

    assert (
        client.get(
            "/internal/v1/eval/config-presets",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        client.post(
            "/internal/v1/eval/config-presets",
            json={"name": "x", "config": {}},
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        client.get(
            f"/internal/v1/eval/config-presets/{preset_id}",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
