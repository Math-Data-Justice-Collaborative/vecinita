"""Unit coverage for DM admin feedback list + write client (F68)."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_data_management_backend.write_client import (
    InternalWriteClient,
    InternalWriteClientError,
)
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.internal_write import FeedbackListResponse

from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

pytestmark = pytest.mark.unit

_PROXY_KEY = "test-proxy-key"
_WRITE_FAIL_MSG = "list_feedback failed: 502 boom"


@pytest.fixture
def auth_key(monkeypatch: pytest.MonkeyPatch) -> EllipticCurvePrivateKey:
    """Inject ES256 test JWKS for admin routes."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key, internal_api_key="test-internal-key")
    monkeypatch.setattr("vecinita_shared_schemas.auth._default_config", cfg)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    return private_key


class _OkFeedbackClient:
    def list_feedback(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
    ) -> FeedbackListResponse:
        _ = (page, page_size, category)
        return FeedbackListResponse(
            items=[],
            page=1,
            page_size=20,
            total_count=0,
        )


class _FailFeedbackClient:
    def list_feedback(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
    ) -> FeedbackListResponse:
        _ = (page, page_size, category)
        raise InternalWriteClientError(_WRITE_FAIL_MSG)


def test_admin_feedback_lists_rows(auth_key: EllipticCurvePrivateKey) -> None:
    """GET /admin/feedback returns 200 for admin JWT."""
    client = TestClient(
        create_app(
            store=InMemoryJobStore(),
            require_proxy_auth=True,
            eval_runs_client=_OkFeedbackClient(),  # type: ignore[arg-type]
        )
    )
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    resp = client.get(
        "/admin/feedback",
        headers={"Authorization": f"Bearer {sign_test_jwt(auth_key, role='admin')}"},
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["total_count"] == 0


def test_admin_feedback_unavailable_without_client(
    auth_key: EllipticCurvePrivateKey,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /admin/feedback returns 503 when write client is missing."""
    monkeypatch.setattr(
        "vecinita_data_management_backend.app._default_eval_runs_client",
        lambda: None,
    )
    client = TestClient(
        create_app(
            store=InMemoryJobStore(),
            require_proxy_auth=True,
        )
    )
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    resp = client.get(
        "/admin/feedback",
        headers={"Authorization": f"Bearer {sign_test_jwt(auth_key, role='admin')}"},
    )
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_admin_feedback_maps_write_client_error(
    auth_key: EllipticCurvePrivateKey,
) -> None:
    """GET /admin/feedback maps InternalWriteClientError to 502."""
    client = TestClient(
        create_app(
            store=InMemoryJobStore(),
            require_proxy_auth=True,
            eval_runs_client=_FailFeedbackClient(),  # type: ignore[arg-type]
        )
    )
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    resp = client.get(
        "/admin/feedback",
        headers={"Authorization": f"Bearer {sign_test_jwt(auth_key, role='admin')}"},
    )
    assert resp.status_code == HTTPStatus.BAD_GATEWAY


def test_write_client_list_feedback_success() -> None:
    """InternalWriteClient.list_feedback parses FeedbackListResponse."""
    feedback_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/internal/v1/feedback"
        assert request.url.params["page"] == "1"
        return httpx.Response(
            HTTPStatus.OK,
            json={
                "items": [
                    {
                        "id": str(feedback_id),
                        "created_at": datetime.now(UTC).isoformat(),
                        "category": "suggestion",
                        "message": "hello",
                        "locale": "en",
                    }
                ],
                "page": 1,
                "page_size": 20,
                "total_count": 1,
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://write.test")
    client = InternalWriteClient(
        base_url="https://write.test",
        api_key="test-key",
        http_client=http_client,
    )
    page = client.list_feedback()
    assert page.total_count == 1
    assert page.items[0].id == feedback_id


def test_write_client_list_feedback_with_category() -> None:
    """Category query param is forwarded."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["category"] == "bug"
        return httpx.Response(
            HTTPStatus.OK,
            json={"items": [], "page": 1, "page_size": 20, "total_count": 0},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://write.test")
    client = InternalWriteClient(
        base_url="https://write.test",
        api_key="test-key",
        http_client=http_client,
    )
    page = client.list_feedback(category="bug")
    assert page.total_count == 0


def test_write_client_list_feedback_raises_on_error() -> None:
    """Non-2xx list_feedback raises InternalWriteClientError."""

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(HTTPStatus.BAD_GATEWAY, text="down")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://write.test")
    client = InternalWriteClient(
        base_url="https://write.test",
        api_key="test-key",
        http_client=http_client,
    )
    with pytest.raises(InternalWriteClientError, match="list_feedback"):
        _ = client.list_feedback()
