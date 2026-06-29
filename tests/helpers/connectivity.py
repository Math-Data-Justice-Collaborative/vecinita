"""Shared assertions for staging connectivity (H4/H5)."""

from __future__ import annotations

import re

import httpx

from tests.helpers.json_response import header_str


def assert_cors_preflight(  # noqa: PLR0913  # mirrors CORS preflight request fields; all keyword-only
    *,
    api_base: str,
    origin: str,
    path: str,
    method: str = "POST",
    extra_request_headers: list[str] | None = None,
    timeout: float = 30.0,
) -> None:
    """OPTIONS preflight must return Access-Control-Allow-Origin for browser clients."""
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": method,
    }
    if extra_request_headers:
        headers["Access-Control-Request-Headers"] = ", ".join(extra_request_headers)
    response = httpx.options(
        f"{api_base.rstrip('/')}{path}",
        headers=headers,
        timeout=timeout,
    )
    assert response.status_code in (200, 204), (
        f"CORS preflight {response.status_code}: {response.text[:200]}"
    )
    allow_origin = header_str(response.headers, "access-control-allow-origin")
    assert allow_origin in (origin, "*"), (
        f"Expected Access-Control-Allow-Origin {origin!r}, got {allow_origin!r}"
    )
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert method.upper() in allow_methods or "*" in allow_methods, (
        f"CORS must allow {method!r}; got access-control-allow-methods={allow_methods!r}"
    )


def fetch_main_js_url(frontend_base: str, timeout: float = 30.0) -> str:
    """Resolve the Vite main bundle URL from deployed index.html."""
    index = httpx.get(f"{frontend_base.rstrip('/')}/", timeout=timeout)
    index.raise_for_status()
    match = re.search(r'src="(/assets/index-[^"]+\.js)"', index.text)
    assert match, "Could not find Vite index-*.js in frontend HTML"
    return f"{frontend_base.rstrip('/')}{match.group(1)}"


def assert_bundle_contains_hosts(
    js_text: str,
    expected_hosts: list[str],
    *,
    forbidden_substrings: list[str] | None = None,
) -> None:
    """Assert the frontend bundle references expected hosts and no dev URLs."""
    for host in expected_hosts:
        assert host in js_text, f"Expected host {host!r} in frontend bundle"
    for bad in forbidden_substrings or ("localhost:8000", "localhost:8001", "localhost:8002"):
        assert bad not in js_text, f"Forbidden dev URL {bad!r} in production bundle"


def extract_https_hosts(js_text: str) -> list[str]:
    """Return all https:// hosts referenced in the bundle text."""
    return re.findall(r"https://[a-zA-Z0-9._-]+(?:\.[a-zA-Z0-9._-]+)+", js_text)
