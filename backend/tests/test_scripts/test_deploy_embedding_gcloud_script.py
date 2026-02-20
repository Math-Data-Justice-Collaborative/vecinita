"""Unit checks for gcloud embedding deployment helper script."""

from pathlib import Path


SCRIPT_PATH = Path("scripts/deploy_embedding_gcloud.sh")


def test_deploy_script_exists_and_is_shell_script():
    assert SCRIPT_PATH.exists()
    content = SCRIPT_PATH.read_text()
    assert content.startswith("#!/usr/bin/env bash")


def test_deploy_script_contains_required_gcloud_steps():
    content = SCRIPT_PATH.read_text()
    assert "gcloud run deploy" in content
    assert "gcloud run services describe" in content
    assert "docker build" in content
    assert "docker push" in content
