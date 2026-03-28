"""Integration test to verify Supabase instance connectivity."""

import os
from urllib.parse import urlparse

import httpx
import pytest


@pytest.mark.integration
def test_supabase_auth_and_rest_connectivity() -> None:
    supabase_url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    supabase_key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or ""
    )

    if not supabase_url or not supabase_key:
        pytest.skip("SUPABASE_URL and key are required for integration connectivity test")

    hostname = (urlparse(supabase_url).hostname or "").lower()
    if not hostname or hostname in {"test.supabase.co", "example.supabase.co"}:
        pytest.skip("SUPABASE_URL points to a placeholder host, skipping live integration check")

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }

    with httpx.Client(timeout=15.0) as client:
        try:
            auth_health = client.get(f"{supabase_url}/auth/v1/health", headers=headers)
        except httpx.ConnectError as exc:
            pytest.skip(f"Supabase host is unreachable from this environment: {exc}")
        assert auth_health.status_code == 200

        rest_probe = client.get(f"{supabase_url}/rest/v1/", headers=headers)
        assert rest_probe.status_code in (200, 404)
