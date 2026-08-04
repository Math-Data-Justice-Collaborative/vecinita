"""UJ-074 / TC-229: audit list returns actor_email via read-time enrich (F69)."""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    sqlalchemy_scalar_one,
)

from tests.helpers.json_response import (
    json_object_list,
    json_str,
    response_json_object,
)

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_API_KEY = "test-internal-key"
_ACTOR_EMAIL = "operator@example.com"


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def test_uj074_audit_list_includes_actor_email_when_resolvable(
    write_client: TestClient,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-229: GET /internal/v1/audit items include actor_email from Supabase lookup."""
    actor_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    request_id = uuid.uuid4()

    def fake_lookup(user_ids: list[UUID]) -> dict[UUID, str]:
        assert actor_id in user_ids
        return {actor_id: _ACTOR_EMAIL}

    monkeypatch.setattr(
        "vecinita_internal_write_api.app.resolve_actor_emails",
        fake_lookup,
        raising=False,
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO audit_log (
                    id, event_type, entity_type, entity_id, request_id,
                    payload, actor_id, actor_role
                )
                VALUES (
                    :id, 'document.edited', 'document', :entity_id, :request_id,
                    '{}'::jsonb, :actor_id, 'admin'
                )
                """
            ),
            {
                "id": uuid.uuid4(),
                "entity_id": entity_id,
                "request_id": request_id,
                "actor_id": actor_id,
            },
        )

    try:
        resp = write_client.get(
            "/internal/v1/audit",
            params={"entity_id": str(entity_id), "page_size": 10},
            headers=_auth(),
        )
        assert resp.status_code == HTTPStatus.OK
        body = response_json_object(resp)
        items = json_object_list(body, "items")
        assert items
        match = next(item for item in items if json_str(item, "entity_id") == str(entity_id))
        assert "actor_email" in match
        assert json_str(match, "actor_email") == _ACTOR_EMAIL
        assert json_str(match, "actor_id") == str(actor_id)

        with engine.connect() as conn:
            cols = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = 'audit_log'
                        """
                    )
                )
            }
        assert "actor_email" not in cols
        assert "email" not in cols
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM audit_log WHERE entity_id = :id"),
                {"id": entity_id},
            )


def test_uj074_audit_list_actor_email_null_when_unresolved(
    write_client: TestClient,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-229: unresolved actor_id yields actor_email null (UI UUID fallback)."""
    actor_id = uuid.uuid4()
    entity_id = uuid.uuid4()

    def fake_lookup(user_ids: list[UUID]) -> dict[UUID, str]:
        _ = user_ids
        return {}

    monkeypatch.setattr(
        "vecinita_internal_write_api.app.resolve_actor_emails",
        fake_lookup,
        raising=False,
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO audit_log (
                    id, event_type, entity_type, entity_id, request_id,
                    payload, actor_id, actor_role
                )
                VALUES (
                    :id, 'document.edited', 'document', :entity_id, :request_id,
                    '{}'::jsonb, :actor_id, 'admin'
                )
                """
            ),
            {
                "id": uuid.uuid4(),
                "entity_id": entity_id,
                "request_id": uuid.uuid4(),
                "actor_id": actor_id,
            },
        )

    try:
        resp = write_client.get(
            "/internal/v1/audit",
            params={"entity_id": str(entity_id)},
            headers=_auth(),
        )
        assert resp.status_code == HTTPStatus.OK
        items = json_object_list(response_json_object(resp), "items")
        match = next(item for item in items if json_str(item, "entity_id") == str(entity_id))
        assert "actor_email" in match
        assert match["actor_email"] is None
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM audit_log WHERE entity_id = :id"),
                {"id": entity_id},
            )


def test_uj074_audit_write_does_not_persist_email(
    write_client: TestClient,
    engine: Engine,
) -> None:
    """TC-230: ingest path never writes email into audit_log payload or columns."""
    entity_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    resp = write_client.post(
        "/internal/v1/audit/event",
        json={
            "event_type": "user.invited",
            "entity_type": "user",
            "entity_id": str(entity_id),
            "actor_id": str(actor_id),
            "actor_role": "admin",
            "payload": {"action": "invite"},
        },
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.ACCEPTED

    try:
        with engine.connect() as conn:
            row = mapping_row(
                conn.execute(
                    text(
                        """
                        SELECT payload::text AS payload_text
                        FROM audit_log
                        WHERE entity_id = :id
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"id": entity_id},
                )
                .mappings()
                .one()
            )
            count = int(
                str(
                    sqlalchemy_scalar_one(
                        conn.execute(
                            text(
                                """
                                SELECT COUNT(*) FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'audit_log'
                                  AND column_name IN ('actor_email', 'email', 'name')
                                """
                            )
                        )
                    )
                )
            )
        assert "email" not in row_str(row, "payload_text").lower()
        assert count == 0
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM audit_log WHERE entity_id = :id"),
                {"id": entity_id},
            )
