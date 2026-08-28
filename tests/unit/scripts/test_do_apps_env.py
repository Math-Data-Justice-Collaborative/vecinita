"""Unit tests for do_apps env overlays (F83 / ADR-054)."""

from __future__ import annotations

import pytest
import yaml
from deploy.do_apps import STAGING_APP_NAMES, app_names_for_env, specs_for_env

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
        specs_for_env("dev")


def test_staging_spec_names_match_yaml() -> None:
    """YAML name fields match app_names_for_env (no DO API)."""
    expected = set(app_names_for_env("staging"))
    found: set[str] = set()
    for path in specs_for_env("staging"):
        data = yaml.safe_load(path.read_text())
        assert isinstance(data, dict)
        name = data.get("name")
        assert isinstance(name, str)
        found.add(name)
    assert found == expected
