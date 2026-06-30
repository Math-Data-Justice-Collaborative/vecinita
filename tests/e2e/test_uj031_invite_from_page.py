"""UJ-031 / TC-090, TC-092: invite from User Management page + invite-only regression."""

from __future__ import annotations

import json
import os
import tomllib
from http import HTTPStatus
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import text
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_str, response_json_object
from tests.helpers.user_mgmt_e2e import ADMIN_ID, UserMgmtStack, admin_bearer

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "supabase" / "config.toml"


def test_invite_creates_invited_viewer_with_audit(user_mgmt_stack: UserMgmtStack) -> None:
    """TC-090: POST /admin/users/invite creates an invited operator with the assigned role."""
    dm = user_mgmt_stack["dm"]
    engine = user_mgmt_stack["engine"]
    headers = {"Authorization": admin_bearer(user_mgmt_stack)}

    response = dm.post(
        "/admin/users/invite",
        json={"email": "new@example.org", "role": "viewer"},
        headers=headers,
    )
    assert response.status_code == HTTPStatus.CREATED
    body = response_json_object(response)
    assert json_str(body, "email") == "new@example.org"
    assert json_str(body, "role") == "viewer"
    assert json_str(body, "status") == "invited"

    entity_id = UUID(json_str(body, "id"))
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT event_type, actor_id, actor_role, payload "
                    "FROM audit_log WHERE entity_id = :id"
                ),
                {"id": entity_id},
            )
            .mappings()
            .first()
        )
    assert row is not None
    assert row["event_type"] == "user.invited"
    assert row["actor_id"] == ADMIN_ID
    assert row["actor_role"] == "admin"
    payload = as_json_object(cast("object", row["payload"]))
    assert payload.get("role") == "viewer"
    assert "new@example.org" not in json.dumps(payload)


def test_public_signup_still_disabled_regression_tc080() -> None:
    """TC-090 regression: invite-only registration remains enforced (TC-080 / UJ-027)."""
    with _CONFIG_PATH.open("rb") as handle:
        config = tomllib.load(handle)

    auth = cast("dict[str, object]", config["auth"])
    email = cast("dict[str, object]", auth["email"])
    assert auth["enable_signup"] is False
    assert email["enable_signup"] is False
