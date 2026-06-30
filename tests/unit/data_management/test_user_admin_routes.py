"""Unit coverage for `/admin/users*` routes (EV-006 F35).

Reuses the shared GoTrue mock helpers from ``tests.helpers.user_admin_mocks`` so route
handlers, lockout mapping, audit emission, and rate limits are exercised under ``tests/unit``.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.email_test import ResendClient, ResendError
from vecinita_data_management_backend.rate_limit import SlidingWindowRateLimiter
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient

from tests.helpers.json_response import json_list, json_object_get, json_str, response_json_object
from tests.helpers.user_admin_mocks import (
    DEV_BYPASS_SUB as _DEV_BYPASS_SUB,
)
from tests.helpers.user_admin_mocks import (
    INVITE_LIMIT as _INVITE_LIMIT,
)
from tests.helpers.user_admin_mocks import (
    VIEWER_ID as _VIEWER_ID,
)
from tests.helpers.user_admin_mocks import (
    make_client as _make_client,
)
from tests.helpers.user_admin_mocks import (
    seed_users as _seed_users,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from vecinita_shared_schemas.internal_write import AuditEventRequest


@pytest.fixture(autouse=True)
def _auth_off(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
    monkeypatch.setenv(
        "VECINITA_ADMIN_FRONTEND_URL",
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
    )


@pytest.fixture
def captured() -> list[AuditEventRequest]:
    return []


@pytest.fixture
def client(
    captured: list[AuditEventRequest],
) -> Iterator[tuple[TestClient, dict[str, dict[str, object]]]]:
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
    test_client, users = client
    response = test_client.get("/admin/users")
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert len(json_list(body, "users")) == len(users)


def test_list_users_rejects_short_search(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, _ = client
    response = test_client.get("/admin/users", params={"q": "ab"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_invite_user_creates_invited_and_audits(
    client: tuple[TestClient, dict[str, dict[str, object]]],
    captured: list[AuditEventRequest],
) -> None:
    test_client, _ = client
    response = test_client.post(
        "/admin/users/invite",
        json={"email": "new@example.org", "role": "viewer"},
    )
    assert response.status_code == HTTPStatus.CREATED
    assert captured[-1].event_type == "user.invited"


def test_invite_rate_limit_returns_429(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
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


def test_change_role_updates_user(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, _ = client
    response = test_client.patch(f"/admin/users/{_VIEWER_ID}/role", json={"role": "admin"})
    assert response.status_code == HTTPStatus.OK
    assert json_str(response_json_object(response), "role") == "admin"


def test_disable_enable_delete_and_reset_password(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, users = client
    assert test_client.post(f"/admin/users/{_VIEWER_ID}/disable").status_code == HTTPStatus.OK
    assert test_client.post(f"/admin/users/{_VIEWER_ID}/enable").status_code == HTTPStatus.OK
    assert test_client.post(f"/admin/users/{_VIEWER_ID}/reset-password").status_code == (
        HTTPStatus.ACCEPTED
    )
    assert test_client.delete(f"/admin/users/{_VIEWER_ID}").status_code == HTTPStatus.NO_CONTENT
    assert _VIEWER_ID not in users


def test_resend_invite_accepts(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, users = client
    invited_id = str(uuid4())
    users[invited_id] = {"id": invited_id, "email": "pending@example.org"}
    response = test_client.post(f"/admin/users/{invited_id}/resend-invite")
    assert response.status_code == HTTPStatus.ACCEPTED


def test_delete_self_is_blocked_with_409(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, _ = client
    response = test_client.delete(f"/admin/users/{_DEV_BYPASS_SUB}")
    assert response.status_code == HTTPStatus.CONFLICT


def test_routes_return_503_when_admin_client_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    app = create_app(require_proxy_auth=False, admin_client=None)
    with TestClient(app) as test_client:
        response = test_client.get("/admin/users")
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_force_signout_maps_missing_rpc_to_mechanism_unavailable(
    captured: list[AuditEventRequest],
) -> None:
    users = _seed_users()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/signout") or "rpc" in request.url.path:
            return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "missing"})
        return httpx.Response(HTTPStatus.OK, json=users[_VIEWER_ID])

    http = httpx.Client(
        base_url="https://test.supabase.co",
        transport=httpx.MockTransport(handler),
    )
    admin = SupabaseAdminClient(
        base_url="https://test.supabase.co",
        secret_key="test-secret",  # noqa: S106
        http_client=http,
    )
    app = create_app(
        require_proxy_auth=False,
        admin_client=admin,
        audit_emit=captured.append,
    )
    with TestClient(app) as test_client:
        response = test_client.post(f"/admin/users/{_VIEWER_ID}/signout")
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_send_test_email_success_and_unconfigured(
    captured: list[AuditEventRequest],
) -> None:
    users = _seed_users()

    def resend_handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.resend.com":
            return httpx.Response(HTTPStatus.OK, json={"id": "re_unit_test"})
        return httpx.Response(HTTPStatus.NOT_FOUND)

    resend = ResendClient(
        api_key="re_test",
        sender="noreply@example.org",
        http_client=httpx.Client(transport=httpx.MockTransport(resend_handler)),
    )
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=captured.append,
        resend_client=resend,
    )
    with TestClient(app) as test_client:
        ok = test_client.post("/admin/email/test", json={"to": "ops@example.org"})
        assert ok.status_code == HTTPStatus.ACCEPTED
        assert json_str(response_json_object(ok), "message_id") == "re_unit_test"

        unconfigured = create_app(
            require_proxy_auth=False,
            admin_client=_make_client(users),
            resend_client=None,
        )
    with TestClient(unconfigured) as test_client:
        blocked = test_client.post("/admin/email/test", json={"to": "ops@example.org"})
    assert blocked.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_send_test_email_maps_resend_errors(
    captured: list[AuditEventRequest],
) -> None:
    users = _seed_users()

    class FailingResend(ResendClient):
        def send_test_email(self, to: str) -> str:  # noqa: ARG002
            msg = "provider down"
            raise ResendError(msg, status_code=502)

    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=captured.append,
        resend_client=FailingResend(api_key="re_test", sender="noreply@example.org"),
    )
    with TestClient(app) as test_client:
        response = test_client.post("/admin/email/test", json={"to": "ops@example.org"})
    assert response.status_code == HTTPStatus.BAD_GATEWAY


def test_send_test_email_maps_unverified_domain_to_domain_unverified(
    captured: list[AuditEventRequest],
) -> None:
    users = _seed_users()

    class UnverifiedDomainResend(ResendClient):
        def send_test_email(self, to: str) -> str:  # noqa: ARG002
            msg = "domain not verified"
            raise ResendError(
                msg,
                status_code=HTTPStatus.FORBIDDEN,
                provider_message="The example.org domain is not verified.",
            )

    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=captured.append,
        resend_client=UnverifiedDomainResend(
            api_key="re_test",
            sender="noreply@example.org",
        ),
    )
    with TestClient(app) as test_client:
        response = test_client.post("/admin/email/test", json={"to": "ops@example.org"})
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    detail = json_object_get(response_json_object(response), "detail")
    assert json_str(detail, "code") == "domain_unverified"
    assert "not verified" in json_str(detail, "message").lower()


def test_audit_emit_failure_does_not_fail_mutation() -> None:
    def boom(_event: AuditEventRequest) -> None:
        msg = "audit sink down"
        raise RuntimeError(msg)

    users = _seed_users()
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=boom,
    )
    with TestClient(app) as test_client:
        response = test_client.post(
            "/admin/users/invite",
            json={"email": "audit-fail@example.org", "role": "viewer"},
        )
    assert response.status_code == HTTPStatus.CREATED


def test_invite_duplicate_active_user_conflicts(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, _ = client
    response = test_client.post(
        "/admin/users/invite",
        json={"email": "viewer@example.org", "role": "viewer"},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_change_role_lockout_returns_409(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, _ = client
    response = test_client.patch(
        f"/admin/users/{_DEV_BYPASS_SUB}/role",
        json={"role": "viewer"},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_list_users_upstream_error_maps_to_502() -> None:
    users = _seed_users()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/v1/admin/users" and request.method == "GET":
            return httpx.Response(HTTPStatus.BAD_GATEWAY, json={"msg": "upstream"})
        return httpx.Response(HTTPStatus.OK, json=users[_VIEWER_ID])

    http = httpx.Client(
        base_url="https://test.supabase.co",
        transport=httpx.MockTransport(handler),
    )
    admin = SupabaseAdminClient(
        base_url="https://test.supabase.co",
        secret_key="test-secret",  # noqa: S106
        http_client=http,
    )
    app = create_app(require_proxy_auth=False, admin_client=admin)
    with TestClient(app) as test_client:
        response = test_client.get("/admin/users")
    assert response.status_code == HTTPStatus.BAD_GATEWAY


def test_email_test_rate_limit_returns_429(
    captured: list[AuditEventRequest],
) -> None:
    users = _seed_users()
    resend = ResendClient(
        api_key="re_test",
        sender="noreply@example.org",
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(HTTPStatus.OK, json={"id": "re_ok"}),
            ),
        ),
    )
    limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=3600)
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=captured.append,
        resend_client=resend,
        email_test_limiter=limiter,
    )
    with TestClient(app) as test_client:
        first = test_client.post("/admin/email/test", json={"to": "ops@example.org"})
        second = test_client.post("/admin/email/test", json={"to": "ops2@example.org"})
    assert first.status_code == HTTPStatus.ACCEPTED
    assert second.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_get_user_not_found_returns_404(
    client: tuple[TestClient, dict[str, dict[str, object]]],
) -> None:
    test_client, _ = client
    response = test_client.post(f"/admin/users/{UUID(int=999)}/disable")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_invite_passes_redirect_to_accept_invite() -> None:
    """TC-104: invite includes redirect_to={origin}/accept-invite on GoTrue outbound."""
    outbound: list[dict[str, object]] = []
    users = _seed_users()
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users, outbound=outbound),
        audit_emit=lambda _event: None,
        invite_limiter=SlidingWindowRateLimiter(max_events=_INVITE_LIMIT, window_seconds=3600),
    )
    with TestClient(app) as test_client:
        response = test_client.post(
            "/admin/users/invite",
            json={"email": "redirect@example.org", "role": "viewer"},
        )
    assert response.status_code == HTTPStatus.CREATED
    assert outbound[-1]["redirect_to"] == (
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/accept-invite"
    )


def test_resend_invite_passes_redirect_to_accept_invite() -> None:
    """TC-104: resend-invite includes redirect_to on GoTrue outbound."""
    outbound: list[dict[str, object]] = []
    users = _seed_users()
    invited_id = str(uuid4())
    users[invited_id] = {"id": invited_id, "email": "pending@example.org"}
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users, outbound=outbound),
        audit_emit=lambda _event: None,
    )
    with TestClient(app) as test_client:
        response = test_client.post(f"/admin/users/{invited_id}/resend-invite")
    assert response.status_code == HTTPStatus.ACCEPTED
    assert outbound[-1]["redirect_to"] == (
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/accept-invite"
    )
def test_reset_password_passes_redirect_to_reset_password() -> None:
    """TC-105: admin recovery includes redirect_to={origin}/reset-password."""
    outbound: list[dict[str, object]] = []
    users = _seed_users()
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users, outbound=outbound),
        audit_emit=lambda _event: None,
    )
    with TestClient(app) as test_client:
        response = test_client.post(f"/admin/users/{_VIEWER_ID}/reset-password")
    assert response.status_code == HTTPStatus.ACCEPTED
    assert outbound[-1]["redirect_to"] == (
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/reset-password"
    )


def test_invite_returns_503_when_admin_frontend_url_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-104: missing VECINITA_ADMIN_FRONTEND_URL yields 503 on invite."""
    monkeypatch.delenv("VECINITA_ADMIN_FRONTEND_URL", raising=False)
    users = _seed_users()
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(users),
        audit_emit=lambda _event: None,
    )
    with TestClient(app) as test_client:
        response = test_client.post(
            "/admin/users/invite",
            json={"email": "missing-env@example.org", "role": "viewer"},
        )
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE

