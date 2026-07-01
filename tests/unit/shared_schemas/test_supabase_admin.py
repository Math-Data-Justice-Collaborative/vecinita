"""EV-006 F35 — Supabase GoTrue Admin REST client (ADR-030 §2, TP-S005-02).

All requests are mocked via httpx.MockTransport — no network and no real Supabase project.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID

import httpx
import pytest
from vecinita_shared_schemas.supabase_admin import (
    SupabaseAdminClient,
    SupabaseAdminError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_BASE = "https://test.supabase.co"
_SECRET = "sb_secret_test"  # noqa: S105  # test fixture value, not a real secret
_UID = "11111111-1111-1111-1111-111111111111"
_HTTP_CONFLICT = 409
_EXPECTED_USERS = 2


def _gotrue_user(
    *,
    uid: str = _UID,
    email: str = "op@example.org",
    role: str | None = "viewer",
    banned: bool = False,
    confirmed: bool = True,
) -> dict[str, object]:
    return {
        "id": uid,
        "email": email,
        "app_metadata": {"role": role} if role is not None else {},
        "banned_until": "2999-01-01T00:00:00Z" if banned else None,
        "created_at": "2026-06-29T00:00:00Z",
        "last_sign_in_at": "2026-06-29T01:00:00Z" if confirmed else None,
        "email_confirmed_at": "2026-06-29T00:30:00Z" if confirmed else None,
        "invited_at": "2026-06-29T00:00:00Z",
    }


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> SupabaseAdminClient:
    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url=_BASE, transport=transport)
    return SupabaseAdminClient(base_url=_BASE, secret_key=_SECRET, http_client=http)


def test_requires_url_and_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Client construction fails when SUPABASE_URL/SECRET_KEY are absent."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    with pytest.raises(SupabaseAdminError):
        SupabaseAdminClient()


def test_list_users_sends_auth_headers_and_parses() -> None:
    """list_users sends apikey + bearer, paginates, and derives user status."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["apikey"] = request.headers.get("apikey")
        captured["auth"] = request.headers.get("authorization")
        captured["page"] = request.url.params.get("page")
        return httpx.Response(
            200,
            json={
                "users": [
                    _gotrue_user(),
                    _gotrue_user(uid="22222222-2222-2222-2222-222222222222", banned=True),
                ]
            },
            headers={"x-total-count": "2"},
        )

    result = _client(handler).list_users(page=2, per_page=25)
    assert captured["method"] == "GET"
    assert captured["path"] == "/auth/v1/admin/users"
    assert captured["apikey"] == _SECRET
    assert captured["auth"] == f"Bearer {_SECRET}"
    assert captured["page"] == "2"
    assert len(result.users) == _EXPECTED_USERS
    assert result.users[0].role == "viewer"
    assert result.users[0].status == "active"
    assert result.users[1].status == "disabled"
    assert result.total == _EXPECTED_USERS


def test_list_users_passes_filter() -> None:
    """A non-empty user_filter is forwarded as the GoTrue filter query param."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["filter"] = request.url.params.get("filter")
        return httpx.Response(200, json={"users": []})

    _client(handler).list_users(user_filter="alice")
    assert captured["filter"] == "alice"


def test_invite_user_posts_to_invite_endpoint() -> None:
    """invite_user_by_email POSTs /auth/v1/invite and returns an invited user."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        captured["redirect_to"] = request.url.params.get("redirect_to")
        return httpx.Response(200, json=_gotrue_user(email="new@example.org", confirmed=False))

    user = _client(handler).invite_user_by_email(
        "new@example.org", redirect_to="https://app/accept-invite"
    )
    assert captured["method"] == "POST"
    assert captured["path"] == "/auth/v1/invite"
    assert captured["redirect_to"] == "https://app/accept-invite"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["email"] == "new@example.org"
    assert user.email == "new@example.org"
    assert user.status == "invited"


def test_update_user_sets_role_via_app_metadata() -> None:
    """update_user_by_id writes role into app_metadata via PUT."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_gotrue_user(role="admin"))

    user = _client(handler).update_user_by_id(UUID(_UID), role="admin")
    assert captured["method"] == "PUT"
    assert captured["path"] == f"/auth/v1/admin/users/{_UID}"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["app_metadata"] == {"role": "admin"}
    assert user.role == "admin"


def test_update_user_ban_duration_disables() -> None:
    """A ban_duration update yields disabled status."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_gotrue_user(banned=True))

    user = _client(handler).update_user_by_id(UUID(_UID), ban_duration="876000h")
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["ban_duration"] == "876000h"
    assert user.status == "disabled"


def test_delete_user_calls_delete() -> None:
    """delete_user issues DELETE to the admin user path."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        return httpx.Response(200, json={})

    _client(handler).delete_user(UUID(_UID))
    assert captured["method"] == "DELETE"
    assert captured["path"] == f"/auth/v1/admin/users/{_UID}"


def test_send_password_recovery_passes_redirect_to() -> None:
    """send_password_recovery forwards redirect_to as a query param (TC-105)."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["redirect_to"] = request.url.params.get("redirect_to")
        return httpx.Response(200, json={})

    _client(handler).send_password_recovery(
        "op@example.org",
        redirect_to="https://app/reset-password",
    )
    assert captured["path"] == "/auth/v1/recover"
    assert captured["redirect_to"] == "https://app/reset-password"


def test_generate_link_recovery() -> None:
    """generate_link posts the link type and returns the action link."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"action_link": "https://app/recover#token"})

    link = _client(handler).generate_link("recovery", "op@example.org")
    assert captured["path"] == "/auth/v1/admin/generate_link"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["type"] == "recovery"
    assert link == "https://app/recover#token"


def test_non_2xx_raises_with_status_code() -> None:
    """Non-2xx responses raise SupabaseAdminError carrying the status code."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"msg": "already registered"})

    with pytest.raises(SupabaseAdminError) as excinfo:
        _client(handler).invite_user_by_email("dup@example.org")
    assert excinfo.value.status_code == _HTTP_CONFLICT


def test_delete_user_sessions_posts_rpc() -> None:
    """delete_user_sessions issues POST to the admin_delete_user_sessions RPC."""
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["method"] = request.method
        return httpx.Response(204)

    _client(handler).delete_user_sessions(UUID(_UID))
    assert captured["method"] == "POST"
    assert captured["path"] == "/rest/v1/rpc/admin_delete_user_sessions"


def test_invited_status_without_confirmation() -> None:
    """Users without confirmation timestamps are parsed as invited."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_gotrue_user(confirmed=False, role="viewer"),
        )

    user = _client(handler).get_user_by_id(UUID(_UID))
    assert user.status == "invited"


def test_malformed_gotrue_payload_raises() -> None:
    """Malformed GoTrue payloads raise SupabaseAdminError during parsing."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": 123, "email": "op@example.org"})

    with pytest.raises(SupabaseAdminError):
        _client(handler).get_user_by_id(UUID(_UID))


def test_client_close_owned_http_client() -> None:
    """close() is safe when the client owns its httpx session."""
    client = SupabaseAdminClient(base_url=_BASE, secret_key=_SECRET)
    client.close()
