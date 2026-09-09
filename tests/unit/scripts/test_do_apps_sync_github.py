"""Tests for syncing DO static_site github.branch from YAML into live specs."""

from __future__ import annotations

from typing import cast

import pytest
from deploy.do_apps import sync_static_site_github_from_yaml

pytestmark = pytest.mark.unit


def test_sync_static_site_github_updates_branch() -> None:
    """Live main branch is overwritten from YAML stage (staging FE retarget)."""
    live = cast(
        "dict[str, object]",
        {
            "name": "vecinita-staging-chat-fe",
            "static_sites": [
                {
                    "name": "web",
                    "github": {
                        "repo": "Math-Data-Justice-Collaborative/vecinita",
                        "branch": "main",
                        "deploy_on_push": False,
                    },
                }
            ],
        },
    )
    desired = cast(
        "dict[str, object]",
        {
            "name": "vecinita-staging-chat-fe",
            "static_sites": [
                {
                    "name": "web",
                    "github": {
                        "repo": "Math-Data-Justice-Collaborative/vecinita",
                        "branch": "stage",
                        "deploy_on_push": False,
                    },
                }
            ],
        },
    )
    changed = sync_static_site_github_from_yaml(live, desired)
    assert changed is True
    sites = cast("list[dict[str, object]]", live["static_sites"])
    github = cast("dict[str, object]", sites[0]["github"])
    assert github["branch"] == "stage"


def test_sync_static_site_github_noop_when_already_matching() -> None:
    """No apps.update when github.branch already matches YAML."""
    live = cast(
        "dict[str, object]",
        {
            "static_sites": [
                {
                    "name": "web",
                    "github": {"repo": "o/r", "branch": "stage", "deploy_on_push": False},
                }
            ],
        },
    )
    desired = cast(
        "dict[str, object]",
        {
            "static_sites": [
                {
                    "name": "web",
                    "github": {"repo": "o/r", "branch": "stage", "deploy_on_push": False},
                }
            ],
        },
    )
    assert sync_static_site_github_from_yaml(live, desired) is False
