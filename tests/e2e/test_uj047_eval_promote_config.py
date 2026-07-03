"""UJ-047 / TC-131-TC-132: super-admin promote + admin deny (e2e layer)."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests
from vecinita_shared_schemas.db_mapping import scalar_int, sqlalchemy_scalar_one
from vecinita_shared_schemas.eval_config import EvalConfig

from tests.helpers.json_response import json_int, json_str, response_json_object
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

_PROMOTED_PROMPT = "Promoted production system prompt for UJ-047."


@pytest.fixture
def promote_config_e2e_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, EllipticCurvePrivateKey, str]]:
    """Write API TestClient + signing key for promote config journeys."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key))
    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rag_production_config"))
        conn.execute(text("DELETE FROM audit_log WHERE event_type = 'rag.config.promoted'"))
    app = create_app()
    with TestClient(app) as client:
        yield client, private_key, database_url
    reset_auth_config_for_tests()


_PROMOTED_TOP_K = 7


def _insert_preset(database_url: str, *, owner_id: UUID) -> UUID:
    preset_id = uuid4()
    config = EvalConfig(
        top_k=_PROMOTED_TOP_K,
        min_retrieval_score=0.25,
        system_prompt=_PROMOTED_PROMPT,
        max_tokens=128,
        temperature=0.1,
        corpus_profile="fixture",
        model_id="qwen2.5:1.5b-instruct",
    ).model_dump(mode="json")
    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_config_presets (
                    id, preset_name, config, shared, owner_id, version
                )
                VALUES (
                    :id, 'promote-fixture', CAST(:config AS jsonb), false, :owner_id, 1
                )
                """
            ),
            {
                "id": preset_id,
                "config": json.dumps(config),
                "owner_id": owner_id,
            },
        )
    return preset_id


def test_tc131_super_admin_promote_updates_active_config_and_audit(
    promote_config_e2e_client: tuple[TestClient, EllipticCurvePrivateKey, str],
) -> None:
    """TC-131: super-admin promote sets active row and writes audit entry."""
    client, private_key, database_url = promote_config_e2e_client
    super_admin_id = uuid4()
    token = sign_test_jwt(private_key, sub=super_admin_id, role="super-admin")
    preset_id = _insert_preset(database_url, owner_id=super_admin_id)

    response = client.post(
        "/internal/v1/rag/config/promote",
        headers={"Authorization": f"Bearer {token}"},
        json={"source": "preset", "preset_id": str(preset_id)},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_int(body, "config_version") == 1
    assert json_str(body, "promoted_by") == str(super_admin_id)

    active = client.get(
        "/internal/v1/rag/config/active",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert active.status_code == HTTPStatus.OK
    active_body = response_json_object(active)
    config = active_body["config"]
    assert isinstance(config, dict)
    assert config["system_prompt"] == _PROMOTED_PROMPT
    assert config["top_k"] == _PROMOTED_TOP_K

    engine = create_engine(database_url)
    with engine.connect() as conn:
        audit_count = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        """
                    SELECT COUNT(*)
                    FROM audit_log
                    WHERE event_type = 'rag.config.promoted'
                    """
                    )
                )
            )
        )
    assert audit_count == 1


def test_tc132_admin_denied_promote(
    promote_config_e2e_client: tuple[TestClient, EllipticCurvePrivateKey, str],
) -> None:
    """TC-132: regular admin cannot promote production config."""
    client, private_key, database_url = promote_config_e2e_client
    admin_id = uuid4()
    admin_token = sign_test_jwt(private_key, sub=admin_id, role="admin")
    preset_id = _insert_preset(database_url, owner_id=admin_id)

    response = client.post(
        "/internal/v1/rag/config/promote",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"source": "preset", "preset_id": str(preset_id)},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN

    active = client.get(
        "/internal/v1/rag/config/active",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert active.status_code == HTTPStatus.NOT_FOUND
