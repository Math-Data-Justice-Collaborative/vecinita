"""Contract tests for scripts/env_sync.py GitHub Actions secret preset."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_SYNC_SCRIPT = REPO_ROOT / "scripts" / "env_sync.py"


@pytest.fixture(scope="module")
def env_sync_module():
    spec = importlib.util.spec_from_file_location("env_sync_script", ENV_SYNC_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.contract
def test_build_github_actions_secrets_bundle_prefers_canonical_modal(env_sync_module):
    data = {
        "MODAL_TOKEN_ID": "tid",
        "MODAL_API_TOKEN_ID": "ignored",
        "MODAL_TOKEN_SECRET": "tsec",
        "DATABASE_URL": "postgresql://a/b",
    }
    b = env_sync_module.build_github_actions_secrets_bundle(data)
    assert b["MODAL_TOKEN_ID"] == "tid"
    assert b["MODAL_TOKEN_SECRET"] == "tsec"
    assert b["DATABASE_URL"] == "postgresql://a/b"


@pytest.mark.contract
def test_build_github_actions_secrets_bundle_modal_api_aliases(env_sync_module):
    data = {
        "MODAL_API_TOKEN_ID": "aid",
        "MODAL_API_TOKEN_SECRET": "asec",
        "DB_URL": "postgresql://x/y",
    }
    b = env_sync_module.build_github_actions_secrets_bundle(data)
    assert b == {
        "MODAL_TOKEN_ID": "aid",
        "MODAL_TOKEN_SECRET": "asec",
        "DATABASE_URL": "postgresql://x/y",
    }


@pytest.mark.contract
def test_build_github_actions_secrets_bundle_auth_legacy(env_sync_module):
    data = {"MODAL_AUTH_KEY": "k", "MODAL_AUTH_SECRET": "s"}
    b = env_sync_module.build_github_actions_secrets_bundle(data)
    assert b == {"MODAL_TOKEN_ID": "k", "MODAL_TOKEN_SECRET": "s"}


@pytest.mark.contract
def test_env_sync_gh_github_actions_preset_dry_run(tmp_path):
    env_file = tmp_path / "ci.env"
    env_file.write_text(
        "MODAL_API_TOKEN_ID=from_api_id\nMODAL_API_TOKEN_SECRET=from_api_secret\n"
        "DATABASE_URL=postgresql://u:p@h/db\nMODAL_PROFILE=myworkspace\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        [
            sys.executable,
            str(ENV_SYNC_SCRIPT),
            "gh",
            "--preset",
            "github-actions",
            "--file",
            str(env_file),
            "--dry-run",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    out = r.stdout
    assert "MODAL_TOKEN_ID" in out
    assert "MODAL_TOKEN_SECRET" in out
    assert "DATABASE_URL" in out
    assert "MODAL_API_PROFILE" in out
