"""T43.2 — first-admin seed script idempotent + sets app_metadata.role=admin (mocked admin API)."""

from __future__ import annotations

from typing import Self, cast

import httpx
import pytest
from scripts.seed_first_admin import (
    seed_first_admin,
)

pytestmark = pytest.mark.unit

_STUB_SUPABASE_KEY = "stub-supabase-key"
_STUB_ADMIN_CREDENTIAL = "stub-admin-credential"


def test_seed_first_admin_creates_user_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test seed first admin creates user when missing."""
    calls: list[tuple[str, str]] = []

    class FakeClient:
        """FakeClient."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Init  ."""
            _ = (args, kwargs)

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            _ = args

        def get(self, path: str, **kwargs: object) -> httpx.Response:
            """Get."""
            _ = kwargs
            calls.append(("GET", path))
            return httpx.Response(200, json={"users": []})

        def post(self, path: str, **kwargs: object) -> httpx.Response:
            """Post."""
            _ = kwargs
            calls.append(("POST", path))
            return httpx.Response(
                200,
                json={"user": {"id": "11111111-1111-1111-1111-111111111111"}},
            )

        def put(self, path: str, **_kwargs: object) -> httpx.Response:
            """Put."""
            _ = (path, _kwargs)
            return httpx.Response(200, json={})

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = seed_first_admin(
        supabase_url="https://test.supabase.co",
        secret_key=_STUB_SUPABASE_KEY,
        email="admin@vecinita.admin",
        password=_STUB_ADMIN_CREDENTIAL,
    )
    assert result.startswith("created")
    assert ("POST", "/auth/v1/admin/users") in calls


def test_seed_first_admin_updates_role_when_user_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test seed first admin updates role when user exists."""
    user_id = "22222222-2222-2222-2222-222222222222"

    class FakeClient:
        """FakeClient."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Init  ."""
            _ = (args, kwargs)

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            _ = args

        def get(self, path: str, **kwargs: object) -> httpx.Response:
            """Get."""
            _ = (path, kwargs)
            return httpx.Response(
                200,
                json={"users": [{"id": user_id, "email": "admin@vecinita.admin"}]},
            )

        def post(self, path: str, **kwargs: object) -> httpx.Response:
            """Post."""
            _ = (path, kwargs)
            msg = "should not create when user exists"
            raise AssertionError(msg)

        def put(self, path: str, **_kwargs: object) -> httpx.Response:
            """Put."""
            assert path == f"/auth/v1/admin/users/{user_id}"
            body = cast("dict[str, object]", _kwargs.get("json"))
            assert body == {"app_metadata": {"role": "admin"}}
            return httpx.Response(200, json={})

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = seed_first_admin(
        supabase_url="https://test.supabase.co",
        secret_key=_STUB_SUPABASE_KEY,
        email="admin@vecinita.admin",
        password=_STUB_ADMIN_CREDENTIAL,
    )
    assert result == f"updated_role:{user_id}"


def test_seed_first_admin_idempotent_on_duplicate_create(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test seed first admin idempotent on duplicate create."""
    user_id = "33333333-3333-3333-3333-333333333333"
    list_calls = 0

    class FakeClient:
        """FakeClient."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Init  ."""
            _ = (args, kwargs)

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            _ = args

        def get(self, path: str, **kwargs: object) -> httpx.Response:
            """Get."""
            nonlocal list_calls
            _ = (path, kwargs)
            list_calls += 1
            if list_calls == 1:
                return httpx.Response(200, json={"users": []})
            return httpx.Response(
                200,
                json={"users": [{"id": user_id, "email": "admin@vecinita.admin"}]},
            )

        def post(self, path: str, **kwargs: object) -> httpx.Response:
            """Post."""
            _ = (path, kwargs)
            return httpx.Response(422, json={"error": "duplicate"})

        def put(self, path: str, **_kwargs: object) -> httpx.Response:
            """Put."""
            assert path == f"/auth/v1/admin/users/{user_id}"
            return httpx.Response(200, json={})

    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = seed_first_admin(
        supabase_url="https://test.supabase.co",
        secret_key=_STUB_SUPABASE_KEY,
        email="admin@vecinita.admin",
        password=_STUB_ADMIN_CREDENTIAL,
    )
    assert result == f"updated_role:{user_id}"
