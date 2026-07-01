"""EV-007 F35 — admin auth redirect URL builder (ADR-032 §2-3, TC-104/105)."""

from __future__ import annotations

from typing import cast

import pytest
from vecinita_data_management_backend.auth_redirect import (
    AdminRedirectConfigError,
    AuthCallbackPath,
    admin_frontend_origin_from_env,
    build_auth_redirect_path,
)


def test_build_auth_redirect_path_strips_trailing_slash() -> None:
    """Valid origin builds accept-invite and reset-password paths."""
    origin = "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/"
    assert build_auth_redirect_path(origin, "accept-invite") == (
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/accept-invite"
    )
    assert build_auth_redirect_path(origin.rstrip("/"), "reset-password") == (
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/reset-password"
    )


def test_build_auth_redirect_path_rejects_invalid_path() -> None:
    """Invalid callback path names raise AdminRedirectConfigError."""
    origin = "https://admin.example.com"
    with pytest.raises(AdminRedirectConfigError, match="Invalid auth callback path"):
        build_auth_redirect_path(origin, cast(AuthCallbackPath, "login"))


def test_build_auth_redirect_path_rejects_invalid_origin() -> None:
    """Malformed origins raise AdminRedirectConfigError."""
    with pytest.raises(AdminRedirectConfigError, match="Invalid admin frontend origin"):
        build_auth_redirect_path("not-a-url", "accept-invite")


def test_admin_frontend_origin_from_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing VECINITA_ADMIN_FRONTEND_URL raises AdminRedirectConfigError."""
    monkeypatch.delenv("VECINITA_ADMIN_FRONTEND_URL", raising=False)
    with pytest.raises(AdminRedirectConfigError, match="VECINITA_ADMIN_FRONTEND_URL"):
        admin_frontend_origin_from_env()


def test_admin_frontend_origin_from_env_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configured origin is returned without trailing slash."""
    monkeypatch.setenv(
        "VECINITA_ADMIN_FRONTEND_URL",
        "https://admin.example.org/",
    )
    assert admin_frontend_origin_from_env() == "https://admin.example.org"
