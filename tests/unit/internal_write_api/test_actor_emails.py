"""Unit tests for F69 read-time actor_email resolution (TC-229)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import httpx
from vecinita_internal_write_api.actor_emails import (
    ActorEmailResolver,
    reset_actor_email_cache_for_tests,
    resolve_actor_emails,
)
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

_BASE = "https://test.supabase.co"
_SECRET = "sb_secret_test"  # noqa: S105  # test fixture value, not a real secret
_UID = UUID("11111111-1111-1111-1111-111111111111")
_EMAIL = "operator@example.com"


def _gotrue_user(*, uid: UUID = _UID, email: str = _EMAIL) -> dict[str, object]:
    return {
        "id": str(uid),
        "email": email,
        "app_metadata": {"role": "admin"},
        "banned_until": None,
        "created_at": "2026-08-04T00:00:00Z",
        "last_sign_in_at": "2026-08-04T01:00:00Z",
        "email_confirmed_at": "2026-08-04T00:30:00Z",
    }


def _admin(handler: Callable[[httpx.Request], httpx.Response]) -> SupabaseAdminClient:
    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url=_BASE, transport=transport)
    return SupabaseAdminClient(base_url=_BASE, secret_key=_SECRET, http_client=http)


def test_resolve_actor_emails_returns_email_for_known_ids() -> None:
    """Known actor_ids map to Supabase emails."""
    reset_actor_email_cache_for_tests()
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json=_gotrue_user())

    result = resolve_actor_emails([_UID], client=_admin(handler))
    assert result == {_UID: _EMAIL}
    assert calls == [f"/auth/v1/admin/users/{_UID}"]


def test_resolve_actor_emails_omits_unresolved_ids() -> None:
    """404 / Admin errors leave the id out of the map (caller sets null)."""
    reset_actor_email_cache_for_tests()

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(404, json={"msg": "not found"})

    result = resolve_actor_emails([_UID], client=_admin(handler))
    assert result == {}


def test_resolve_actor_emails_skips_empty_and_dedupes() -> None:
    """Empty input is a no-op; duplicate ids are fetched once."""
    reset_actor_email_cache_for_tests()
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json=_gotrue_user())

    assert resolve_actor_emails([], client=_admin(handler)) == {}
    result = resolve_actor_emails([_UID, _UID], client=_admin(handler))
    assert result == {_UID: _EMAIL}
    assert len(calls) == 1


def test_resolve_actor_emails_uses_ttl_cache() -> None:
    """Second resolve for the same id hits cache (no second Admin call)."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json=_gotrue_user())

    resolver = ActorEmailResolver(client=_admin(handler))
    assert resolver.resolve([_UID]) == {_UID: _EMAIL}
    assert resolver.resolve([_UID]) == {_UID: _EMAIL}
    assert len(calls) == 1


def test_resolve_actor_emails_without_client_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing Supabase config yields empty map (emails stay null)."""
    reset_actor_email_cache_for_tests()
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    other = uuid4()
    assert resolve_actor_emails([other]) == {}


def test_actor_email_resolver_negative_cache() -> None:
    """Failed lookups are cached as misses so we do not hammer Admin API."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(404, json={"msg": "not found"})

    resolver = ActorEmailResolver(client=_admin(handler))
    assert resolver.resolve([_UID]) == {}
    assert resolver.resolve([_UID]) == {}
    assert len(calls) == 1


def test_resolve_actor_emails_omits_user_with_empty_email() -> None:
    """GoTrue user without email is treated as unresolved (omit from map)."""
    reset_actor_email_cache_for_tests()

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, json=_gotrue_user(email=""))

    result = resolve_actor_emails([_UID], client=_admin(handler))
    assert result == {}
