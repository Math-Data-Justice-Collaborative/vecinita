"""EV-006 F35 (ADR-031 §TP-S005-20) — GET /admin/users?q= search guard (TC-100, UJ-030).

A non-empty ``q`` shorter than 3 chars is rejected with ``400 invalid_search``; a valid ``q``
is forwarded to the GoTrue Admin ``filter`` query param; an empty ``q`` lists unfiltered.
The Supabase Admin client is backed by an ``httpx.MockTransport`` GoTrue simulator that records
the upstream query params so forwarding can be asserted.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient

from tests.helpers.json_response import json_object_get, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

_SEED_USERS: list[dict[str, object]] = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "viewer@example.org",
        "app_metadata": {"role": "viewer"},
        "last_sign_in_at": "2026-06-03T00:00:00Z",
    },
]


def _make_handler(seen: list[str | None]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/v1/admin/users" and request.method == "GET":
            seen.append(cast("str | None", request.url.params.get("filter")))
            return httpx.Response(
                HTTPStatus.OK,
                json={"users": _SEED_USERS},
                headers={"x-total-count": str(len(_SEED_USERS))},
            )
        return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "unhandled"})

    return httpx.MockTransport(handler)


def _make_client(seen: list[str | None]) -> SupabaseAdminClient:
    http_client = httpx.Client(
        base_url="https://test.supabase.co",
        transport=_make_handler(seen),
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


@pytest.fixture
def seen() -> list[str | None]:
    """Collect the GoTrue ``filter`` query param seen on each upstream list call."""
    return []


@pytest.fixture
def client(seen: list[str | None]) -> Iterator[TestClient]:
    """TestClient wired through a mocked Supabase Admin client that records list filters."""
    app = create_app(
        require_proxy_auth=False,
        admin_client=_make_client(seen),
        audit_emit=lambda _event: None,
    )
    with TestClient(app) as test_client:
        yield test_client


def test_short_query_returns_400_invalid_search(client: TestClient) -> None:
    """A non-empty q shorter than 3 chars is rejected with 400 invalid_search."""
    response = client.get("/admin/users", params={"q": "ab"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    detail = json_object_get(response_json_object(response), "detail")
    assert json_str(detail, "code") == "invalid_search"


def test_valid_query_is_forwarded_to_gotrue_filter(
    client: TestClient,
    seen: list[str | None],
) -> None:
    """A q of >=3 chars is forwarded to the GoTrue admin filter param."""
    response = client.get("/admin/users", params={"q": "viewer"})
    assert response.status_code == HTTPStatus.OK
    assert seen[-1] == "viewer"


def test_empty_query_lists_unfiltered(client: TestClient, seen: list[str | None]) -> None:
    """An absent/empty q lists operators without a GoTrue filter."""
    response = client.get("/admin/users")
    assert response.status_code == HTTPStatus.OK
    assert seen[-1] is None
