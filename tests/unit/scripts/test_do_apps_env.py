"""Unit tests for do_apps env overlays (F83 / ADR-054)."""

from __future__ import annotations

from typing import cast

import pytest
import yaml
from deploy.do_apps import (
    STAGING_APP_NAMES,
    app_names_for_env,
    specs_for_env,
    validate_prod_cors_origins,
)

pytestmark = pytest.mark.unit

_DO_APP_NAME_MAX = 32


def test_specs_for_env_prod_uses_infra_do_root() -> None:
    """Prod specs live under infra/do (not staging/)."""
    paths = specs_for_env("prod")
    assert all(p.parent.name == "do" for p in paths)
    assert any(p.name == "chat-rag-backend.yaml" for p in paths)


def test_specs_for_env_staging_uses_staging_dir() -> None:
    """Staging specs live under infra/do/staging and all files exist."""
    paths = specs_for_env("staging")
    assert all(p.parent.name == "staging" for p in paths)
    assert len(paths) == len(STAGING_APP_NAMES)
    for path in paths:
        assert path.is_file(), f"missing staging spec: {path}"


def test_app_names_for_env_staging_short_names() -> None:
    """Staging DO app names stay within the 32-character platform limit."""
    names = app_names_for_env("staging")
    assert names == list(STAGING_APP_NAMES)
    assert all(len(n) <= _DO_APP_NAME_MAX for n in names)


def test_specs_for_env_rejects_unknown() -> None:
    """Only prod and staging are valid env selectors."""
    with pytest.raises(ValueError, match="env"):
        _ = specs_for_env("dev")


def test_staging_spec_names_match_yaml() -> None:
    """YAML name fields match app_names_for_env (no DO API)."""
    expected = set(app_names_for_env("staging"))
    found: set[str] = set()
    for path in specs_for_env("staging"):
        data = cast("dict[str, object]", yaml.safe_load(path.read_text()))
        name = data.get("name")
        assert isinstance(name, str)
        found.add(name)
    assert found == expected


def test_validate_prod_cors_origins_rejects_staging_only() -> None:
    """BUG-2026-09-10: sync must refuse staging-only CORS on prod backends."""
    with pytest.raises(SystemExit, match="staging frontend"):
        validate_prod_cors_origins(
            "vecinita-chat-rag-backend",
            "https://vecinita-staging-chat-fe-epvwo.ondigitalocean.app",
        )


def test_validate_prod_cors_origins_rejects_prod_plus_staging() -> None:
    """Prod+staging combo must fail (ADR-054 isolation; security review)."""
    cors = (
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app,"
        + "https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app,"
        + "https://vecinita-staging-chat-fe-epvwo.ondigitalocean.app"
    )
    with pytest.raises(SystemExit, match="staging frontend"):
        validate_prod_cors_origins("vecinita-chat-rag-backend", cors)


def test_validate_prod_cors_origins_ignores_shell_staging_fe_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shell FE URLs must not redefine the required prod hosts (Bugbot)."""
    monkeypatch.setenv(
        "VECINITA_CHAT_FRONTEND_URL",
        "https://vecinita-staging-chat-fe-epvwo.ondigitalocean.app",
    )
    monkeypatch.setenv(
        "VECINITA_ADMIN_FRONTEND_URL",
        "https://vecinita-staging-admin-fe-4tj2p.ondigitalocean.app",
    )
    # Canonical prod pair still passes even when shell FE aliases are staging.
    validate_prod_cors_origins(
        "vecinita-internal-write-api",
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app,"
        + "https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app",
    )


def test_validate_prod_cors_origins_accepts_prod_pair() -> None:
    """Prod chat+admin FE origins are accepted for prod API sync."""
    validate_prod_cors_origins(
        "vecinita-internal-write-api",
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app,"
        + "https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app",
    )


def test_validate_prod_cors_origins_skips_staging_apps() -> None:
    """Staging write-api may keep staging FE origins."""
    validate_prod_cors_origins(
        "vecinita-staging-write-api",
        "https://vecinita-staging-chat-fe-epvwo.ondigitalocean.app",
    )
