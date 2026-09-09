"""Smoke: staging FE bundles must include environment banner (F83 / UX-1)."""

from __future__ import annotations

import os
import re
from http import HTTPStatus

import httpx
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.live]


def _fe_bases() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    chat = (os.environ.get("VECINITA_STAGING_CHAT_FRONTEND_URL") or "").strip().rstrip("/")
    admin = (os.environ.get("VECINITA_STAGING_ADMIN_FRONTEND_URL") or "").strip().rstrip("/")
    if chat:
        out.append(("chat", chat))
    if admin:
        out.append(("admin", admin))
    return out


@pytest.mark.skipif(not _fe_bases(), reason="VECINITA_STAGING_*_FRONTEND_URL unset")
def test_staging_fe_js_includes_environment_banner() -> None:
    """Live staging FE must ship EnvironmentBanner marker after deploy wait."""
    failures: list[str] = []
    for label, base in _fe_bases():
        html_resp = httpx.get(f"{base}/", timeout=30.0)
        html_resp.raise_for_status()
        match = re.search(r"""src=["']([^"']*assets/[^"']+\.js)["']""", html_resp.text)
        if match is None:
            failures.append(f"{label}: no assets/*.js in index HTML")
            continue
        asset = match.group(1)
        js_url = asset if asset.startswith("http") else f"{base}{asset}"
        js_resp = httpx.get(js_url, timeout=60.0)
        if js_resp.status_code >= HTTPStatus.BAD_REQUEST:
            failures.append(f"{label}: fetch {js_url} failed: {js_resp.status_code}")
            continue
        js = js_resp.text
        if "environment-banner" not in js and "envBanner" not in js:
            failures.append(
                f"{label}: bundle missing environment banner "
                "(Deploy Staging likely returned before FE ACTIVE)"
            )
    assert not failures, "; ".join(failures)
