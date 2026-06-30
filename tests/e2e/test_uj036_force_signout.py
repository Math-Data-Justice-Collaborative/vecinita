"""UJ-036 / TC-098: admin force sign-out of another operator."""

from __future__ import annotations

import json
import os
from http import HTTPStatus

import pytest
from sqlalchemy import text

from tests.helpers.json_response import response_json_object
from tests.helpers.user_mgmt_e2e import VIEWER_ID, UserMgmtStack, admin_bearer, viewer_bearer

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]


def test_admin_force_signout_audited_without_pii(user_mgmt_stack: UserMgmtStack) -> None:
    """TC-098: admin force-signout returns 202 and persists a PII-free audit row."""
    dm = user_mgmt_stack["dm"]
    engine = user_mgmt_stack["engine"]
    headers = {"Authorization": admin_bearer(user_mgmt_stack)}

    response = dm.post(f"/admin/users/{VIEWER_ID}/signout", headers=headers)
    assert response.status_code == HTTPStatus.ACCEPTED
    assert response_json_object(response)["acknowledged"] is True

    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT event_type, entity_type, payload "
                    "FROM audit_log WHERE entity_id = :id ORDER BY created_at DESC LIMIT 1"
                ),
                {"id": VIEWER_ID},
            )
            .mappings()
            .first()
        )
    assert row is not None
    assert row["event_type"] == "user.signed_out"
    assert row["entity_type"] == "user"
    assert "@" not in json.dumps(row["payload"])


def test_viewer_cannot_force_signout(user_mgmt_stack: UserMgmtStack) -> None:
    """TC-098: viewer JWT is rejected from the force-signout route."""
    dm = user_mgmt_stack["dm"]
    headers = {"Authorization": viewer_bearer(user_mgmt_stack)}
    response = dm.post(f"/admin/users/{VIEWER_ID}/signout", headers=headers)
    assert response.status_code == HTTPStatus.FORBIDDEN
