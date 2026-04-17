"""Contract tests for scripts/env_sync.py GitHub Actions secret preset."""

from __future__ import annotations

import importlib.util
import json
import os
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
        "MODAL_AUTH_KEY": "ignored",
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
        "MODAL_TOKEN_ID": "aid",
        "MODAL_TOKEN_SECRET": "asec",
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
def test_build_render_runtime_modal_bundle_aliases_and_extras(env_sync_module):
    data = {
        "MODAL_TOKEN_ID": "aid",
        "MODAL_TOKEN_SECRET": "asec",
        "MODAL_FUNCTION_INVOCATION": "auto",
        "EMBEDDING_SERVICE_AUTH_TOKEN": "embedtok",
    }
    b = env_sync_module.build_render_runtime_modal_bundle(data)
    assert b == {
        "MODAL_TOKEN_ID": "aid",
        "MODAL_TOKEN_SECRET": "asec",
        "MODAL_FUNCTION_INVOCATION": "auto",
        "EMBEDDING_SERVICE_AUTH_TOKEN": "embedtok",
    }


@pytest.mark.contract
def test_resolve_render_service_id_finds_web_service(env_sync_module, monkeypatch):
    payload = [{"name": "vecinita-gateway", "id": "srv-abc", "serviceType": "web"}]

    def fake_run(cmd, capture_output, text, check):
        assert cmd == ["render", "services", "-o", "json"]
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(env_sync_module.subprocess, "run", fake_run)
    assert env_sync_module.resolve_render_service_id("vecinita-gateway") == "srv-abc"


@pytest.mark.contract
def test_resolve_render_service_id_items_wrapper(env_sync_module, monkeypatch):
    payload = {"items": [{"name": "svc-x", "id": "srv-wrap", "serviceType": "web"}]}

    def fake_run(cmd, capture_output, text, check):
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(env_sync_module.subprocess, "run", fake_run)
    assert env_sync_module.resolve_render_service_id("svc-x") == "srv-wrap"


@pytest.mark.contract
def test_env_sync_render_api_preset_dry_run_no_shell_api_key(tmp_path):
    env_file = tmp_path / "r.env"
    env_file.write_text(
        "RENDER_API_KEY=rk_test_only_in_file\n"
        "MODAL_TOKEN_ID=id1\n"
        "MODAL_TOKEN_SECRET=s1\n"
        "MODAL_FUNCTION_INVOCATION=auto\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        [
            sys.executable,
            str(ENV_SYNC_SCRIPT),
            "render-api",
            "--preset",
            "render-runtime-modal",
            "--file",
            str(env_file),
            "--service-id",
            "srv-testfake",
            "--dry-run",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={k: v for k, v in os.environ.items() if k != "RENDER_API_KEY"},
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "MODAL_TOKEN_ID" in r.stdout
    assert "MODAL_FUNCTION_INVOCATION" in r.stdout
    assert "srv-testfake" in r.stdout


@pytest.mark.contract
def test_env_sync_gh_github_actions_preset_dry_run(tmp_path):
    env_file = tmp_path / "ci.env"
    env_file.write_text(
        "MODAL_TOKEN_ID=from_api_id\nMODAL_TOKEN_SECRET=from_api_secret\n"
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
