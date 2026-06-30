"""EV-006 F35 (ADR-031 §TP-S005-19) — POST /admin/users/{id}/signout (TC-098, UJ-036).

Force sign-out revokes the target operator's sessions via the ``admin_delete_user_sessions``
RPC, is admin-gated, emits a PII-free ``user.signed_out`` audit, and degrades to
``503 mechanism_unavailable`` when the RPC has not been applied to the Supabase project.
The Supabase Admin client is backed by an ``httpx.MockTransport`` so the route, audit, and
RPC-absent mapping are exercised without a live project.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient

from tests.helpers.json_response import json_object_get, json_str, response_json_object
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from vecinita_shared_schemas.internal_write import AuditEventRequest

_TARGET_ID = "11111111-1111-1111-1111-111111111111"
_RPC_PATH = "/rest/v1/rpc/admin_delete_user_sessions"


def _make_handler(*, rpc_applied: bool) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == _RPC_PATH and request.method == "POST":
            if not rpc_applied:
                # PostgREST returns 404 (PGRST202) when the function does not exist.
                return httpx.Response(HTTPStatus.NOT_FOUND, json={"code": "PGRST202"})
            return httpx.Response(HTTPStatus.NO_CONTENT)
        return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "unhandled"})

    return httpx.MockTransport(handler)


def _make_client(*, rpc_applied: bool) -> SupabaseAdminClient:
    http_client = httpx.Client(
        base_url="https://test.supabase.co",
        transport=_make_handler(rpc_applied=rpc_applied),
    )
    return SupabaseAdminClient(
        base_url="https://test.supabase.co",
        secret_key="test-secret",  # noqa: S106  # test fixture, not a real secret
        http_client=http_client,
    )


@pytest.fixture(autouse=True)
def _auth_off(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
    yield
    reset_auth_config_for_tests()


def test_force_signout_admin_returns_202_and_audits() -> None:
    """An admin force-signs-out a target; returns 202 and emits a PII-free user.signed_out."""
    captured: list[AuditEventRequest] = []
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(rpc_applied=True),
        audit_emit=captured.append,
    )
    with TestClient(app) as client:
        response = client.post(f"/admin/users/{_TARGET_ID}/signout")
    assert response.status_code == HTTPStatus.ACCEPTED
    assert response_json_object(response)["acknowledged"] is True
    assert captured[-1].event_type == "user.signed_out"
    assert captured[-1].entity_type == "user"
    assert str(captured[-1].entity_id) == _TARGET_ID
    assert "@" not in json.dumps(captured[-1].payload)


def test_force_signout_rpc_absent_returns_503_mechanism_unavailable() -> None:
    """When the RPC is not applied, the route degrades to 503 mechanism_unavailable."""
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(rpc_applied=False),
        audit_emit=lambda _event: None,
    )
    with TestClient(app) as client:
        response = client.post(f"/admin/users/{_TARGET_ID}/signout")
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    detail = json_object_get(response_json_object(response), "detail")
    assert json_str(detail, "code") == "mechanism_unavailable"


def test_force_signout_viewer_jwt_is_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """A viewer operator JWT is rejected from the admin namespace with 403 (TC-098)."""
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    private_key = generate_es256_keypair()
    set_auth_config_for_tests(make_auth_config(private_key, auth_required=True))
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(rpc_applied=True),
        audit_emit=lambda _event: None,
    )
    token = sign_test_jwt(private_key, role="viewer")
    with TestClient(app) as client:
        response = client.post(
            f"/admin/users/{_TARGET_ID}/signout",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == HTTPStatus.FORBIDDEN
