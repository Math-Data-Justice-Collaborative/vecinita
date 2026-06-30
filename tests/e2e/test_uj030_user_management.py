"""UJ-030 / TC-088, TC-089, TC-092: admin user management lifecycle, viewer block, audit."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from uuid import UUID

import pytest
from sqlalchemy import text
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object
from tests.helpers.user_mgmt_e2e import (
    ADMIN_ID,
    SECOND_ADMIN_ID,
    VIEWER_ID,
    UserMgmtStack,
    admin_bearer,
    viewer_bearer,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]


def _admin_headers(stack: UserMgmtStack) -> dict[str, str]:
    return {"Authorization": admin_bearer(stack)}


def _viewer_headers(stack: UserMgmtStack) -> dict[str, str]:
    return {"Authorization": viewer_bearer(stack)}


def test_admin_lists_operators_and_mutates_lifecycle(user_mgmt_stack: UserMgmtStack) -> None:
    """TC-088: admin can list and run the full operator lifecycle via /admin/users*."""
    dm = user_mgmt_stack["dm"]
    headers = _admin_headers(user_mgmt_stack)

    listed = dm.get("/admin/users", headers=headers)
    assert listed.status_code == HTTPStatus.OK
    body = response_json_object(listed)
    assert len(json_list(body, "users")) >= 2

    invited = dm.post(
        "/admin/users/invite",
        json={"email": "new-op@example.org", "role": "viewer"},
        headers=headers,
    )
    assert invited.status_code == HTTPStatus.CREATED
    invited_id = json_str(response_json_object(invited), "id")

    role_changed = dm.patch(
        f"/admin/users/{VIEWER_ID}/role",
        json={"role": "admin"},
        headers=headers,
    )
    assert role_changed.status_code == HTTPStatus.OK

    resent = dm.post(f"/admin/users/{invited_id}/resend-invite", headers=headers)
    assert resent.status_code == HTTPStatus.ACCEPTED

    disabled = dm.post(f"/admin/users/{VIEWER_ID}/disable", headers=headers)
    assert disabled.status_code == HTTPStatus.OK
    assert json_str(response_json_object(disabled), "status") == "disabled"

    enabled = dm.post(f"/admin/users/{VIEWER_ID}/enable", headers=headers)
    assert enabled.status_code == HTTPStatus.OK
    assert json_str(response_json_object(enabled), "status") == "active"

    reset = dm.post(f"/admin/users/{VIEWER_ID}/reset-password", headers=headers)
    assert reset.status_code == HTTPStatus.ACCEPTED

    deleted = dm.delete(f"/admin/users/{invited_id}", headers=headers)
    assert deleted.status_code == HTTPStatus.NO_CONTENT


def test_viewer_forbidden_on_admin_users_namespace(user_mgmt_stack: UserMgmtStack) -> None:
    """TC-089: viewer JWT is rejected from every /admin/users* write and list."""
    dm = user_mgmt_stack["dm"]
    headers = _viewer_headers(user_mgmt_stack)
    target = str(SECOND_ADMIN_ID)

    assert dm.get("/admin/users", headers=headers).status_code == HTTPStatus.FORBIDDEN
    assert (
        dm.post(
            "/admin/users/invite",
            json={"email": "blocked@example.org", "role": "viewer"},
            headers=headers,
        ).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        dm.patch(f"/admin/users/{target}/role", json={"role": "viewer"}, headers=headers).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert (
        dm.post(f"/admin/users/{target}/resend-invite", headers=headers).status_code
        == HTTPStatus.FORBIDDEN
    )
    assert dm.post(f"/admin/users/{target}/disable", headers=headers).status_code == HTTPStatus.FORBIDDEN
    assert dm.post(f"/admin/users/{target}/enable", headers=headers).status_code == HTTPStatus.FORBIDDEN
    assert dm.delete(f"/admin/users/{target}", headers=headers).status_code == HTTPStatus.FORBIDDEN
    assert (
        dm.post(f"/admin/users/{target}/reset-password", headers=headers).status_code
        == HTTPStatus.FORBIDDEN
    )


def _audit_row(engine: Engine, entity_id: UUID) -> dict[str, object] | None:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT event_type, entity_type, actor_id, actor_role, payload "
                    "FROM audit_log WHERE entity_id = :id ORDER BY created_at DESC LIMIT 1"
                ),
                {"id": entity_id},
            )
            .mappings()
            .first()
        )
    if row is None:
        return None
    return dict(row)


def test_user_management_mutations_audited_without_pii(user_mgmt_stack: UserMgmtStack) -> None:
    """TC-092: each mutation persists an audit row with opaque actor and no PII payload."""
    dm = user_mgmt_stack["dm"]
    engine = user_mgmt_stack["engine"]
    headers = _admin_headers(user_mgmt_stack)

    invite = dm.post(
        "/admin/users/invite",
        json={"email": "audit-target@example.org", "role": "viewer"},
        headers=headers,
    )
    assert invite.status_code == HTTPStatus.CREATED
    entity_id = UUID(json_str(response_json_object(invite), "id"))

    row = _audit_row(engine, entity_id)
    assert row is not None
    assert row["event_type"] == "user.invited"
    assert row["entity_type"] == "user"
    assert row["actor_id"] == ADMIN_ID
    assert row["actor_role"] == "admin"
    payload = as_json_object(cast("object", row["payload"]))
    assert "email" not in payload
    assert "name" not in payload
    assert "audit-target@example.org" not in json.dumps(payload)

    dm.patch(f"/admin/users/{entity_id}/role", json={"role": "admin"}, headers=headers)
    role_row = _audit_row(engine, entity_id)
    assert role_row is not None
    assert role_row["event_type"] == "user.role_changed"
    role_payload = as_json_object(cast("object", role_row["payload"]))
    assert "email" not in role_payload

    dm.delete(f"/admin/users/{entity_id}", headers=headers)
    delete_row = _audit_row(engine, entity_id)
    assert delete_row is not None
    assert delete_row["event_type"] == "user.deleted"
