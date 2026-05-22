"""H4/H5 live staging: CORS + frontend bundle wiring (connectivity-gates.md)."""

from __future__ import annotations

import os

import httpx
import pytest
from tests.helpers.connectivity import (
    assert_bundle_contains_hosts,
    assert_cors_preflight,
    fetch_main_js_url,
)

pytestmark = [pytest.mark.e2e, pytest.mark.live]


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


@pytest.fixture
def chat_api() -> str:
    url = _env("VECINITA_STAGING_CHAT_URL")
    if not url:
        pytest.skip("Set VECINITA_STAGING_CHAT_URL")
    return url.rstrip("/")


@pytest.fixture
def chat_frontend() -> str:
    url = _env("VECINITA_STAGING_CHAT_FRONTEND_URL")
    if not url:
        pytest.skip("Set VECINITA_STAGING_CHAT_FRONTEND_URL for H5")
    return url.rstrip("/")


@pytest.fixture
def admin_frontend() -> str:
    url = _env("VECINITA_STAGING_ADMIN_FRONTEND_URL")
    if not url:
        pytest.skip("Set VECINITA_STAGING_ADMIN_FRONTEND_URL for H5")
    return url.rstrip("/")


def test_h4_chat_backend_cors_preflight(chat_api: str, chat_frontend: str) -> None:
    assert_cors_preflight(
        api_base=chat_api,
        origin=chat_frontend,
        path="/api/v1/ask/stream",
        method="POST",
        extra_request_headers=["content-type"],
    )


def test_h4_write_api_cors_preflight(admin_frontend: str) -> None:
    write_url = _env("VECINITA_STAGING_WRITE_URL")
    if not write_url:
        pytest.skip("Set VECINITA_STAGING_WRITE_URL")
    assert_cors_preflight(
        api_base=write_url,
        origin=admin_frontend,
        path="/internal/v1/documents",
        method="GET",
        extra_request_headers=["authorization"],
    )


def test_h4_write_api_cors_preflight_delete_document(admin_frontend: str) -> None:
    write_url = _env("VECINITA_STAGING_WRITE_URL")
    if not write_url:
        pytest.skip("Set VECINITA_STAGING_WRITE_URL")
    assert_cors_preflight(
        api_base=write_url,
        origin=admin_frontend,
        path="/internal/v1/documents/00000000-0000-0000-0000-000000000001",
        method="DELETE",
        extra_request_headers=["authorization"],
    )


def test_h4_modal_data_mgmt_cors_preflight(admin_frontend: str) -> None:
    admin_api = _env("VECINITA_STAGING_ADMIN_API_URL")
    if not admin_api:
        pytest.skip("Set VECINITA_STAGING_ADMIN_API_URL for Modal CORS check")
    assert_cors_preflight(
        api_base=admin_api,
        origin=admin_frontend,
        path="/jobs",
        method="POST",
        extra_request_headers=["content-type", "x-vecinita-proxy-key"],
        timeout=60.0,
    )


def test_h5_chat_frontend_bundle_points_at_backend(chat_frontend: str, chat_api: str) -> None:
    js_url = fetch_main_js_url(chat_frontend)
    js = httpx.get(js_url, timeout=30.0).text
    host = httpx.URL(chat_api).host
    assert host
    assert_bundle_contains_hosts(js, [host])


def test_h5_admin_frontend_bundle_has_modal_and_write_hosts(
    admin_frontend: str,
) -> None:
    write_url = _env("VECINITA_STAGING_WRITE_URL")
    admin_api = _env("VECINITA_STAGING_ADMIN_API_URL")
    if not write_url:
        pytest.skip("Set VECINITA_STAGING_WRITE_URL")
    js_url = fetch_main_js_url(admin_frontend)
    js = httpx.get(js_url, timeout=30.0).text
    hosts = [httpx.URL(write_url).host]
    if admin_api:
        hosts.append(httpx.URL(admin_api).host)
    assert all(hosts)
    assert_bundle_contains_hosts(js, [h for h in hosts if h])
