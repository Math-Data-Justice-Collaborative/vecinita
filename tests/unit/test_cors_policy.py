"""H0c: browser CORS policy on FastAPI apps (connectivity-gates.md)."""

from __future__ import annotations

import os
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import (
    create_app as create_chat_app,
)
from vecinita_data_management_backend.app import (
    create_app as create_data_mgmt_app,
)
from vecinita_internal_write_api.app import (
    create_app as create_write_app,
)

from tests.helpers.json_response import (
    header_str,
)

CHAT_ORIGIN = "https://vecinita-chat-rag-frontend.example.com"
ADMIN_ORIGIN = "https://vecinita-admin-frontend.example.com"


@pytest.fixture(autouse=True)
def cors_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Allow both chat and admin frontend origins for every test."""
    monkeypatch.setenv(
        "VECINITA_CORS_ORIGINS",
        f"{CHAT_ORIGIN},{ADMIN_ORIGIN}",
    )


def test_chat_rag_cors_preflight_on_ask_stream() -> None:
    """Chat-rag allows the chat origin to preflight POST /ask/stream."""
    client = TestClient(create_chat_app())
    response = client.options(
        "/api/v1/ask/stream",
        headers={
            "Origin": CHAT_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == CHAT_ORIGIN


def test_chat_rag_cors_preflight_on_browse_documents() -> None:
    """TC-046: OPTIONS on GET /api/v1/documents from chat frontend origin."""
    client = TestClient(create_chat_app())
    response = client.options(
        "/api/v1/documents",
        headers={
            "Origin": CHAT_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == CHAT_ORIGIN


def test_chat_rag_cors_preflight_on_tags() -> None:
    """TC-046: OPTIONS on GET /api/v1/tags from chat frontend origin."""
    client = TestClient(create_chat_app())
    response = client.options(
        "/api/v1/tags",
        headers={
            "Origin": CHAT_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == CHAT_ORIGIN


def test_chat_rag_cors_preflight_on_warm() -> None:
    """S001 T11: OPTIONS on POST /api/v1/warm from chat frontend origin."""
    client = TestClient(create_chat_app())
    response = client.options(
        "/api/v1/warm",
        headers={
            "Origin": CHAT_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == CHAT_ORIGIN


def test_internal_write_cors_preflight_on_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    """Internal write API allows the admin origin to preflight GET /documents."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/documents",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN


def test_internal_write_cors_preflight_allows_delete_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal write API CORS preflight allows DELETE on a document path."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/documents/00000000-0000-0000-0000-000000000001",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "DELETE" in allow_methods


def test_data_management_cors_preflight_on_jobs() -> None:
    """Data-management allows the admin origin to preflight POST /jobs."""
    client = TestClient(
        create_data_mgmt_app(require_proxy_auth=False),
    )
    response = client.options(
        "/jobs",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, x-vecinita-proxy-key",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN


def test_data_management_cors_preflight_on_admin_users_invite() -> None:
    """TC-093: DM allows the admin origin to preflight POST /admin/users/invite."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/admin/users/invite",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN


def test_data_management_cors_preflight_on_admin_users_role_patch() -> None:
    """TC-093: DM CORS preflight allows PATCH on /admin/users/{id}/role."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/admin/users/00000000-0000-0000-0000-000000000001/role",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "PATCH" in allow_methods


def test_data_management_cors_preflight_on_admin_users_delete() -> None:
    """TC-093: DM CORS preflight allows DELETE on /admin/users/{id}."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/admin/users/00000000-0000-0000-0000-000000000001",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "DELETE" in allow_methods


def test_internal_write_cors_preflight_on_document_tags_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal write API CORS preflight allows PATCH on document tags."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/documents/00000000-0000-0000-0000-000000000001/tags",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "PATCH" in allow_methods


def test_internal_write_cors_preflight_on_chunk_tags_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal write API CORS preflight allows PATCH on chunk tags."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/chunks/00000000-0000-0000-0000-000000000001/tags",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "PATCH" in allow_methods


def test_internal_write_cors_preflight_on_eval_runs_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal write API CORS preflight allows POST on eval runs (F36)."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/eval/runs",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "POST" in allow_methods


def test_internal_write_cors_preflight_on_eval_criteria_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal write API CORS preflight allows POST on eval criteria (M64)."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/eval/criteria",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "POST" in allow_methods


def test_internal_write_cors_preflight_on_eval_timeseries_get(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal write API CORS preflight allows GET on eval timeseries (EV-008)."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/eval/runs/timeseries",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "GET" in allow_methods


def test_internal_write_cors_preflight_on_eval_config_presets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EV-009: CORS preflight allows POST/PATCH on eval config preset routes."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    preset_id = "00000000-0000-0000-0000-000000000001"
    for path, method in (
        ("/internal/v1/eval/config-presets", "POST"),
        (f"/internal/v1/eval/config-presets/{preset_id}", "PATCH"),
        (f"/internal/v1/eval/config-presets/{preset_id}/clone", "POST"),
    ):
        response = client.options(
            path,
            headers={
                "Origin": ADMIN_ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert response.status_code == HTTPStatus.OK
        assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
        allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
        assert method in allow_methods


def test_internal_write_cors_preflight_on_rag_config_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EV-009: CORS preflight allows GET/POST on rag production config routes."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    for path, method in (
        ("/internal/v1/rag/config/active", "GET"),
        ("/internal/v1/rag/config/promote", "POST"),
    ):
        response = client.options(
            path,
            headers={
                "Origin": ADMIN_ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert response.status_code == HTTPStatus.OK
        assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
        allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
        assert method in allow_methods


def test_internal_write_cors_preflight_on_ollama_model_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EV-009: CORS preflight allows GET/POST on Ollama model list/pull routes."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    for path, method in (
        ("/internal/v1/models/ollama", "GET"),
        ("/internal/v1/models/ollama/catalog", "GET"),
        ("/internal/v1/models/ollama/catalog/qwen2.5", "GET"),
        ("/internal/v1/models/ollama/pull", "POST"),
    ):
        response = client.options(
            path,
            headers={
                "Origin": ADMIN_ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert response.status_code == HTTPStatus.OK
        assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
        allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
        assert method in allow_methods


def test_no_cors_middleware_when_origins_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """No CORS headers are returned when no allowed origins are configured."""
    monkeypatch.delenv("VECINITA_CORS_ORIGINS", raising=False)
    client = TestClient(create_chat_app())
    response = client.options(
        "/health",
        headers={"Origin": CHAT_ORIGIN, "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_data_management_cors_preflight_on_admin_users_signout() -> None:
    """TC-103: DM CORS preflight allows POST on /admin/users/{id}/signout."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/admin/users/00000000-0000-0000-0000-000000000001/signout",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "POST" in allow_methods


def test_data_management_cors_preflight_on_admin_users_revoke_invite() -> None:
    """TC-103/108: DM CORS preflight allows POST on /admin/users/{id}/revoke-invite."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/admin/users/00000000-0000-0000-0000-000000000001/revoke-invite",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "POST" in allow_methods


def test_data_management_cors_preflight_on_admin_email_test() -> None:
    """TC-103: DM CORS preflight allows POST on /admin/email/test."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/admin/email/test",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "POST" in allow_methods
