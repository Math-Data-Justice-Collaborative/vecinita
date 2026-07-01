"""Shared GoTrue Admin mock fixtures for `/admin/users*` tests (EV-006 F35).

Backs the Supabase Admin client with an ``httpx.MockTransport`` GoTrue simulator so the
route layer, lockout-guard mapping, audit emission, and rate limit can be exercised
without a live Supabase project. Imported by both the integration and unit suites.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import cast
from uuid import uuid4

import httpx
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient

from tests.helpers.json_response import json_str

DEV_BYPASS_SUB = "00000000-0000-0000-0000-000000000000"
VIEWER_ID = "11111111-1111-1111-1111-111111111111"
SECOND_ADMIN_ID = "22222222-2222-2222-2222-222222222222"
BANNED_UNTIL = "2125-01-01T00:00:00Z"
INVITE_LIMIT = 2


def seed_users() -> dict[str, dict[str, object]]:
    """Two admins (dev-bypass actor + spare) and one active viewer."""
    return {
        DEV_BYPASS_SUB: {
            "id": DEV_BYPASS_SUB,
            "email": "actor@example.org",
            "app_metadata": {"role": "admin"},
            "last_sign_in_at": "2026-06-01T00:00:00Z",
        },
        SECOND_ADMIN_ID: {
            "id": SECOND_ADMIN_ID,
            "email": "spare-admin@example.org",
            "app_metadata": {"role": "admin"},
            "last_sign_in_at": "2026-06-02T00:00:00Z",
        },
        VIEWER_ID: {
            "id": VIEWER_ID,
            "email": "viewer@example.org",
            "app_metadata": {"role": "viewer"},
            "last_sign_in_at": "2026-06-03T00:00:00Z",
        },
    }


def is_active(user: dict[str, object]) -> bool:
    """A GoTrue user is active once confirmed or signed in at least once."""
    return bool(user.get("email_confirmed_at") or user.get("last_sign_in_at"))


def make_handler(  # noqa: C901
    users: dict[str, dict[str, object]],
    *,
    outbound: list[dict[str, object]] | None = None,
) -> httpx.MockTransport:
    """Return a MockTransport simulating the GoTrue admin endpoints over ``users``."""

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
                        "method": method,
                        "redirect_to": request.url.params.get("redirect_to"),
                    },
                )
            email = json_str(as_json_object(cast("object", json.loads(request.content))), "email")
            existing = next((u for u in users.values() if u["email"] == email), None)
            if existing is not None:
                if is_active(existing):
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
                    user["banned_until"] = BANNED_UNTIL
            return httpx.Response(HTTPStatus.OK, json=user)
        if path.startswith("/auth/v1/admin/users/") and method == "DELETE":
            users.pop(path.rsplit("/", 1)[-1], None)
            return httpx.Response(HTTPStatus.OK, json={})
        if path == "/auth/v1/recover" and method == "POST":
            if outbound is not None:
                outbound.append(
                    {
                        "path": path,
                        "method": method,
                        "redirect_to": request.url.params.get("redirect_to"),
                    },
                )
            return httpx.Response(HTTPStatus.OK, json={})
        return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "unhandled"})

    return httpx.MockTransport(handler)


def make_client(
    users: dict[str, dict[str, object]],
    *,
    outbound: list[dict[str, object]] | None = None,
) -> SupabaseAdminClient:
    """Build a SupabaseAdminClient wired to the GoTrue mock transport over ``users``."""
    http_client = httpx.Client(
        base_url="https://test.supabase.co",
        transport=make_handler(users, outbound=outbound),
    )
    return SupabaseAdminClient(
        base_url="https://test.supabase.co",
        secret_key="test-secret",  # noqa: S106  # test fixture, not a real secret
        http_client=http_client,
    )
