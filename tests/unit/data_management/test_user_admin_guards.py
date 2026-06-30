"""EV-006 F35 (ADR-030 §4, TP-S005-04) — UserAdminService lockout guards.

Admins cannot delete/disable/demote their own account or the sole remaining admin.
The Supabase Admin API is mocked via httpx.MockTransport — no network.
"""

from __future__ import annotations

from uuid import UUID

import httpx
import pytest
from vecinita_data_management_backend.user_admin import LockoutError, UserAdminService
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient

_BASE = "https://test.supabase.co"
_SECRET = "sb_secret_test"  # noqa: S105  # test fixture value, not a real secret
_ACTOR = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_OTHER_ADMIN = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_VIEWER = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


def _user_json(uid: UUID, role: str, *, banned: bool = False) -> dict[str, object]:
    return {
        "id": str(uid),
        "email": f"{role}@example.org",
        "app_metadata": {"role": role},
        "banned_until": "2999-01-01T00:00:00Z" if banned else None,
        "email_confirmed_at": "2026-06-29T00:00:00Z",
    }


def _service(*, target: dict[str, object], admins: list[dict[str, object]]) -> UserAdminService:
    """Build a service over a mocked admin client with a fixed target + admin roster."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/auth/v1/admin/users/"):
            if request.method in {"PUT", "DELETE"}:
                return httpx.Response(200, json=target)
            return httpx.Response(200, json=target)
        if request.url.path == "/auth/v1/admin/users":
            return httpx.Response(200, json={"users": admins})
        return httpx.Response(404, json={})

    http = httpx.Client(base_url=_BASE, transport=httpx.MockTransport(handler))
    client = SupabaseAdminClient(base_url=_BASE, secret_key=_SECRET, http_client=http)
    return UserAdminService(client)


def test_count_active_admins_excludes_disabled() -> None:
    """Disabled admins are not counted toward the active-admin total."""
    svc = _service(
        target=_user_json(_ACTOR, "admin"),
        admins=[
            _user_json(_ACTOR, "admin"),
            _user_json(_OTHER_ADMIN, "admin", banned=True),
        ],
    )
    assert svc.count_active_admins() == 1


def test_count_active_admins_paginates_beyond_first_page() -> None:
    """Admin count walks all GoTrue list pages, not only the first per_page=200 slice."""
    page_size = 200
    # Page 1: one active admin + filler viewers; page 2: second active admin.
    page1 = [_user_json(_ACTOR, "admin")] + [
        _user_json(UUID(f"{i:032x}"), "viewer") for i in range(page_size - 1)
    ]
    page2 = [_user_json(_OTHER_ADMIN, "admin")]
    list_calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/v1/admin/users":
            call_index = list_calls["count"]
            list_calls["count"] = call_index + 1
            users = page1 if call_index == 0 else page2
            return httpx.Response(200, json={"users": users})
        return httpx.Response(404, json={})

    http = httpx.Client(base_url=_BASE, transport=httpx.MockTransport(handler))
    client = SupabaseAdminClient(base_url=_BASE, secret_key=_SECRET, http_client=http)
    svc = UserAdminService(client)
    expected_active_admins = 2
    assert svc.count_active_admins() == expected_active_admins


def test_delete_self_blocked() -> None:
    """An admin cannot delete their own account."""
    svc = _service(target=_user_json(_ACTOR, "admin"), admins=[_user_json(_ACTOR, "admin")])
    with pytest.raises(LockoutError) as excinfo:
        svc.delete_user(actor_id=_ACTOR, target_id=_ACTOR)
    assert excinfo.value.code == "self_action"


def test_delete_last_admin_blocked() -> None:
    """Deleting the sole remaining admin is blocked."""
    svc = _service(
        target=_user_json(_OTHER_ADMIN, "admin"),
        admins=[_user_json(_OTHER_ADMIN, "admin")],
    )
    with pytest.raises(LockoutError) as excinfo:
        svc.delete_user(actor_id=_ACTOR, target_id=_OTHER_ADMIN)
    assert excinfo.value.code == "last_admin"


def test_delete_viewer_allowed() -> None:
    """Deleting a viewer (not self, admins remain) is permitted."""
    svc = _service(
        target=_user_json(_VIEWER, "viewer"),
        admins=[_user_json(_ACTOR, "admin"), _user_json(_OTHER_ADMIN, "admin")],
    )
    svc.delete_user(actor_id=_ACTOR, target_id=_VIEWER)


def test_disable_last_admin_blocked() -> None:
    """Disabling the last admin is blocked."""
    svc = _service(
        target=_user_json(_OTHER_ADMIN, "admin"),
        admins=[_user_json(_OTHER_ADMIN, "admin")],
    )
    with pytest.raises(LockoutError) as excinfo:
        svc.disable_user(actor_id=_ACTOR, target_id=_OTHER_ADMIN)
    assert excinfo.value.code == "last_admin"


def test_demote_self_blocked() -> None:
    """An admin cannot demote their own account to viewer."""
    svc = _service(
        target=_user_json(_ACTOR, "admin"),
        admins=[_user_json(_ACTOR, "admin"), _user_json(_OTHER_ADMIN, "admin")],
    )
    with pytest.raises(LockoutError) as excinfo:
        svc.change_role(actor_id=_ACTOR, target_id=_ACTOR, new_role="viewer")
    assert excinfo.value.code == "self_action"


def test_demote_last_admin_blocked() -> None:
    """Demoting the sole remaining admin to viewer is blocked."""
    svc = _service(
        target=_user_json(_OTHER_ADMIN, "admin"),
        admins=[_user_json(_OTHER_ADMIN, "admin")],
    )
    with pytest.raises(LockoutError) as excinfo:
        svc.change_role(actor_id=_ACTOR, target_id=_OTHER_ADMIN, new_role="viewer")
    assert excinfo.value.code == "last_admin"


def test_promote_viewer_allowed() -> None:
    """Promoting a viewer to admin is not guarded."""
    svc = _service(
        target=_user_json(_VIEWER, "viewer"),
        admins=[_user_json(_ACTOR, "admin")],
    )
    user = svc.change_role(actor_id=_ACTOR, target_id=_VIEWER, new_role="admin")
    assert user is not None
