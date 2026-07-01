"""Shared helpers for EV-006 F35 user-management E2E tests (mocked GoTrue Admin API)."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from typing import TYPE_CHECKING, TypedDict, cast
from uuid import UUID, uuid4

import httpx
import pytest  # noqa: TC002 — runtime fixture typing
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests
from vecinita_shared_schemas.internal_write import (
    AuditEventRequest,  # noqa: TC002 — runtime audit_emit
)
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient

from tests.helpers.json_response import json_str
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
    from sqlalchemy.engine import Engine

API_KEY = "test-internal-key"
PROXY_KEY = "test-proxy-key"
ADMIN_ID = UUID("00000000-0000-0000-0000-000000000000")
VIEWER_ID = UUID("11111111-1111-1111-1111-111111111111")
SECOND_ADMIN_ID = UUID("22222222-2222-2222-2222-222222222222")
_BANNED_UNTIL = "2125-01-01T00:00:00Z"


class UserMgmtStack(TypedDict):
    """DM + write API clients, DB engine, and mocked GoTrue user store."""

    dm: TestClient
    write: TestClient
    engine: Engine
    private_key: EllipticCurvePrivateKey
    users: dict[str, dict[str, object]]
    audited_entity_ids: list[UUID]
    outbound: list[dict[str, object]]


def database_url() -> str:
    """Return the integration-test database URL (defaults to local docker-compose)."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def seed_users() -> dict[str, dict[str, object]]:
    """Seed admin, spare admin, and viewer records for mocked GoTrue."""
    return {
        str(ADMIN_ID): {
            "id": str(ADMIN_ID),
            "email": "actor@example.org",
            "app_metadata": {"role": "admin"},
            "last_sign_in_at": "2026-06-01T00:00:00Z",
        },
        str(SECOND_ADMIN_ID): {
            "id": str(SECOND_ADMIN_ID),
            "email": "spare-admin@example.org",
            "app_metadata": {"role": "admin"},
            "last_sign_in_at": "2026-06-02T00:00:00Z",
        },
        str(VIEWER_ID): {
            "id": str(VIEWER_ID),
            "email": "viewer@example.org",
            "app_metadata": {"role": "viewer"},
            "last_sign_in_at": "2026-06-03T00:00:00Z",
        },
    }


def _is_active(user: dict[str, object]) -> bool:
    return bool(user.get("email_confirmed_at") or user.get("last_sign_in_at"))


def make_gotrue_handler(  # noqa: C901
    users: dict[str, dict[str, object]],
    *,
    outbound: list[dict[str, object]] | None = None,
) -> httpx.MockTransport:
    """Build a mock GoTrue Admin API transport backed by an in-memory user map."""

    def handler(request: httpx.Request) -> httpx.Response:  # noqa: C901, PLR0911, PLR0912
        path = request.url.path
        method = request.method
        if path == "/auth/v1/admin/users" and method == "GET":
            items = list(users.values())
            return httpx.Response(
                HTTPStatus.OK,
                json={"users": items},
                headers={"x-total-count": str(len(items))},
            )
        if path.startswith("/auth/v1/admin/users/") and method == "GET":
            uid = path.rsplit("/", 1)[-1]
            user = users.get(uid)
            if user is None:
                return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "not found"})
            return httpx.Response(HTTPStatus.OK, json=user)
        if path == "/auth/v1/invite" and method == "POST":
            if outbound is not None:
                outbound.append(
                    {
                        "path": path,
                        "redirect_to": request.url.params.get("redirect_to"),
                    },
                )
            email = json_str(as_json_object(cast("object", json.loads(request.content))), "email")
            existing = next((u for u in users.values() if u["email"] == email), None)
            if existing is not None:
                if _is_active(existing):
                    return httpx.Response(HTTPStatus.UNPROCESSABLE_ENTITY, json={"msg": "exists"})
                return httpx.Response(HTTPStatus.OK, json=existing)
            new_id = str(uuid4())
            new_user: dict[str, object] = {"id": new_id, "email": email}
            users[new_id] = new_user
            return httpx.Response(HTTPStatus.OK, json=new_user)
        if path.startswith("/auth/v1/admin/users/") and method == "PUT":
            uid = path.rsplit("/", 1)[-1]
            body = as_json_object(cast("object", json.loads(request.content)))
            user = users[uid]
            if "app_metadata" in body:
                user["app_metadata"] = body["app_metadata"]
            if "ban_duration" in body:
                if body["ban_duration"] == "none":
                    user.pop("banned_until", None)
                else:
                    user["banned_until"] = _BANNED_UNTIL
            return httpx.Response(HTTPStatus.OK, json=user)
        if path.startswith("/auth/v1/admin/users/") and method == "DELETE":
            users.pop(path.rsplit("/", 1)[-1], None)
            return httpx.Response(HTTPStatus.OK, json={})
        if path == "/auth/v1/recover" and method == "POST":
            return httpx.Response(HTTPStatus.OK, json={})
        if path == "/rest/v1/rpc/admin_delete_user_sessions" and method == "POST":
            return httpx.Response(HTTPStatus.NO_CONTENT)
        return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "unhandled"})

    return httpx.MockTransport(handler)


def make_admin_client(
    users: dict[str, dict[str, object]],
    *,
    outbound: list[dict[str, object]] | None = None,
) -> SupabaseAdminClient:
    """Wrap the mock transport in a SupabaseAdminClient for DM backend injection."""
    http_client = httpx.Client(
        base_url="https://test.supabase.co",
        transport=make_gotrue_handler(users, outbound=outbound),
    )
    return SupabaseAdminClient(
        base_url="https://test.supabase.co",
        secret_key="test-secret",  # noqa: S106  # test fixture
        http_client=http_client,
    )


def admin_bearer(stack: UserMgmtStack) -> str:
    """Return an Authorization header for the seeded admin operator."""
    token = sign_test_jwt(stack["private_key"], sub=ADMIN_ID, role="admin")
    return f"Bearer {token}"


def viewer_bearer(stack: UserMgmtStack) -> str:
    """Return an Authorization header for the seeded viewer operator."""
    token = sign_test_jwt(stack["private_key"], sub=VIEWER_ID, role="viewer")
    return f"Bearer {token}"


def build_user_mgmt_stack(monkeypatch: pytest.MonkeyPatch) -> Iterator[UserMgmtStack]:
    """Yield DM + write API clients with mocked GoTrue and real audit_log persistence."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    db_url = database_url()
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", PROXY_KEY)
    monkeypatch.setenv(
        "VECINITA_ADMIN_FRONTEND_URL",
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
    )
    set_auth_config_for_tests(make_auth_config(private_key, internal_api_key=API_KEY))

    write_api = TestClient(create_write_app())
    users = seed_users()
    audited_entity_ids: list[UUID] = []
    outbound: list[dict[str, object]] = []

    def audit_emit(event: AuditEventRequest) -> None:
        audited_entity_ids.append(event.entity_id)
        response = write_api.post(
            "/internal/v1/audit/event",
            json=event.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        assert response.status_code == HTTPStatus.ACCEPTED, response.text

    dm_app = create_app(
        store=InMemoryJobStore(),
        require_proxy_auth=True,
        admin_client=make_admin_client(users, outbound=outbound),
        audit_emit=audit_emit,
    )
    dm_client = TestClient(dm_app)
    dm_client.headers.update({"X-Vecinita-Proxy-Key": PROXY_KEY})

    engine = create_engine(db_url)
    stack: UserMgmtStack = {
        "dm": dm_client,
        "write": write_api,
        "engine": engine,
        "private_key": private_key,
        "users": users,
        "audited_entity_ids": audited_entity_ids,
        "outbound": outbound,
    }
    yield stack

    with engine.begin() as conn:
        for entity_id in audited_entity_ids:
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": entity_id})

    reset_auth_config_for_tests()
