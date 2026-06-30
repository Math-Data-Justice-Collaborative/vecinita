"""EV-006 F35 (ADR-030 §1/§3) — `/admin/users*` DM backend routes (TC-088, TC-089).

Drives the real FastAPI app via TestClient. The Supabase Admin client is backed by an
``httpx.MockTransport`` GoTrue simulator so the route layer, lockout-guard mapping, audit
emission, and rate limit are all exercised without a live Supabase project.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.rate_limit import SlidingWindowRateLimiter
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.helpers.json_response import (
    json_list,
    json_object_get,
    json_str,
    response_json_object,
)
from tests.helpers.user_admin_mocks import DEV_BYPASS_SUB as _DEV_BYPASS_SUB
from tests.helpers.user_admin_mocks import INVITE_LIMIT as _INVITE_LIMIT
from tests.helpers.user_admin_mocks import VIEWER_ID as _VIEWER_ID
from tests.helpers.user_admin_mocks import make_client as _make_client
from tests.helpers.user_admin_mocks import seed_users as _seed_users
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from vecinita_shared_schemas.internal_write import AuditEventRequest


@pytest.fixture(autouse=True)
def _auth_off(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
    yield
    reset_auth_config_for_tests()


@pytest.fixture
def captured() -> list[AuditEventRequest]:
    """Collect audit events emitted by the routes under test."""
    return []


@pytest.fixture
def client(
    captured: list[AuditEventRequest],
) -> Iterator[tuple[TestClient, dict[str, dict[str, object]]]]:
    """TestClient + mutable GoTrue user store wired through a mocked Admin client."""
    users = _seed_users()
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=captured.append,
        invite_limiter=SlidingWindowRateLimiter(max_events=_INVITE_LIMIT, window_seconds=3600),
    )
    with TestClient(app) as test_client:
        yield test_client, users


def test_list_users_returns_operators(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    """GET /admin/users returns the operator roster with pagination metadata."""
    test_client, users = client
    response = test_client.get("/admin/users")
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert len(json_list(body, "users")) == len(users)
    assert body["page"] == 1
    assert body["page_size"] != 0


def test_invite_user_creates_invited_and_audits(
    client: tuple[TestClient, dict[str, dict[str, object]]],
    captured: list[AuditEventRequest],
) -> None:
    """POST /admin/users/invite creates an invited user, sets role, and emits a PII-free audit."""
    test_client, _ = client
    response = test_client.post(
        "/admin/users/invite",
        json={"email": "new@example.org", "role": "viewer"},
    )
    assert response.status_code == HTTPStatus.CREATED
    body = response_json_object(response)
    assert json_str(body, "status") == "invited"
    assert json_str(body, "role") == "viewer"
    assert captured[-1].event_type == "user.invited"
    assert "new@example.org" not in json.dumps(captured[-1].payload)


def test_invite_duplicate_active_user_conflicts(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    """Inviting an already-active operator surfaces 409."""
    test_client, _ = client
    response = test_client.post(
        "/admin/users/invite",
        json={"email": "viewer@example.org", "role": "viewer"},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_change_role_updates_user_and_audits(
    client: tuple[TestClient, dict[str, dict[str, object]]],
    captured: list[AuditEventRequest],
) -> None:
    """PATCH /admin/users/{id}/role promotes the viewer and emits user.role_changed."""
    test_client, _ = client
    response = test_client.patch(f"/admin/users/{_VIEWER_ID}/role", json={"role": "admin"})
    assert response.status_code == HTTPStatus.OK
    assert json_str(response_json_object(response), "role") == "admin"
    assert captured[-1].event_type == "user.role_changed"


def test_resend_invite_accepts(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    """POST /admin/users/{id}/resend-invite returns 202 for a pending invitee."""
    test_client, users = client
    invited_id = str(uuid4())
    users[invited_id] = {"id": invited_id, "email": "pending@example.org"}
    response = test_client.post(f"/admin/users/{invited_id}/resend-invite")
    assert response.status_code == HTTPStatus.ACCEPTED


def test_disable_then_enable_round_trips(
    client: tuple[TestClient, dict[str, dict[str, object]]],
    captured: list[AuditEventRequest],
) -> None:
    """Disable bans the viewer (status disabled); enable restores active status."""
    test_client, _ = client
    disabled = test_client.post(f"/admin/users/{_VIEWER_ID}/disable")
    assert disabled.status_code == HTTPStatus.OK
    assert json_str(response_json_object(disabled), "status") == "disabled"
    assert captured[-1].event_type == "user.disabled"

    enabled = test_client.post(f"/admin/users/{_VIEWER_ID}/enable")
    assert enabled.status_code == HTTPStatus.OK
    assert json_str(response_json_object(enabled), "status") == "active"
    assert captured[-1].event_type == "user.enabled"


def test_delete_user_returns_204_and_audits(
    client: tuple[TestClient, dict[str, dict[str, object]]],
    captured: list[AuditEventRequest],
) -> None:
    """DELETE /admin/users/{id} removes a non-self operator and emits user.deleted."""
    test_client, users = client
    response = test_client.delete(f"/admin/users/{_VIEWER_ID}")
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert _VIEWER_ID not in users
    assert captured[-1].event_type == "user.deleted"


def test_reset_password_accepts_and_audits(
    client: tuple[TestClient, dict[str, dict[str, object]]],
    captured: list[AuditEventRequest],
) -> None:
    """POST /admin/users/{id}/reset-password sends recovery and emits user.reset_password."""
    test_client, _ = client
    response = test_client.post(f"/admin/users/{_VIEWER_ID}/reset-password")
    assert response.status_code == HTTPStatus.ACCEPTED
    assert captured[-1].event_type == "user.reset_password"


def test_delete_self_is_blocked_with_409(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    """An admin cannot delete their own account (LockoutError -> 409 self_action)."""
    test_client, _ = client
    response = test_client.delete(f"/admin/users/{_DEV_BYPASS_SUB}")
    assert response.status_code == HTTPStatus.CONFLICT
    detail = json_object_get(response_json_object(response), "detail")
    assert json_str(detail, "code") == "self_action"


def test_invite_rate_limit_returns_429(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    """The (limit+1)th invite within the window is rejected with 429 (TP-S005-07)."""
    test_client, _ = client
    for index in range(_INVITE_LIMIT):
        ok = test_client.post(
            "/admin/users/invite",
            json={"email": f"user{index}@example.org", "role": "viewer"},
        )
        assert ok.status_code == HTTPStatus.CREATED
    blocked = test_client.post(
        "/admin/users/invite",
        json={"email": "overflow@example.org", "role": "viewer"},
    )
    assert blocked.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_viewer_jwt_is_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """A viewer operator JWT is rejected from the admin namespace with 403 (TC-089)."""
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    private_key = generate_es256_keypair()
    set_auth_config_for_tests(make_auth_config(private_key, auth_required=True))
    users = _seed_users()
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=lambda _event: None,
    )
    token = sign_test_jwt(private_key, role="viewer")
    with TestClient(app) as test_client:
        response = test_client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_routes_return_503_when_admin_client_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no Supabase Admin credentials, the namespace reports 503 (not a 500)."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    app = create_app(require_proxy_auth=False, admin_client=None)
    with TestClient(app) as test_client:
        response = test_client.get("/admin/users")
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_get_user_not_found_returns_404(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    """Acting on an unknown user id maps the upstream 404 to a 404 response."""
    test_client, _ = client
    response = test_client.post(f"/admin/users/{UUID(int=999)}/disable")
    assert response.status_code == HTTPStatus.NOT_FOUND
