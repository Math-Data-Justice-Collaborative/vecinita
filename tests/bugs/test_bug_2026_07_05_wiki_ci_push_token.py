"""Regression: Publish Wiki CI must authenticate with WIKI_PUSH_TOKEN for wiki git push."""

from __future__ import annotations

from pathlib import Path

from scripts.docs.sync_github_wiki import build_wiki_remote_url

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github/workflows/publish-wiki.yml"


def test_build_wiki_remote_url_uses_x_access_token_for_github_token() -> None:
    """GITHUB_TOKEN-style values use x-access-token auth in the remote URL."""
    actions_token = "ghs_" + "actions_token"
    url = build_wiki_remote_url(
        repository="org/repo",
        token=actions_token,
        actor="github-actions[bot]",
    )
    assert url == f"https://x-access-token:{actions_token}@github.com/org/repo.wiki.git"


def test_build_wiki_remote_url_uses_actor_for_classic_pat() -> None:
    """Classic PATs (ghp_*) embed actor:token in the remote URL."""
    url = build_wiki_remote_url(
        repository="org/repo",
        token="ghp_" + "a" * 36,
        actor="my-user",
    )
    assert url == f"https://my-user:ghp_{'a' * 36}@github.com/org/repo.wiki.git"


def test_build_wiki_remote_url_uses_actor_for_fine_grained_pat() -> None:
    """Fine-grained PATs (github_pat_*) embed actor:token in the remote URL."""
    token = "github_pat_" + "b" * 22
    url = build_wiki_remote_url(
        repository="Math-Data-Justice-Collaborative/vecinita",
        token=token,
        actor="deploy-bot",
    )
    assert (
        url
        == f"https://deploy-bot:{token}@github.com/Math-Data-Justice-Collaborative/vecinita.wiki.git"
    )


def test_publish_wiki_workflow_prefers_wiki_push_token_secret() -> None:
    """Matches CI failure run 28750906126 — GITHUB_TOKEN alone cannot push to *.wiki.git."""
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "secrets.WIKI_PUSH_TOKEN" in content
    assert "secrets.WIKI_PUSH_TOKEN || secrets.GITHUB_TOKEN" in content


def test_publish_wiki_workflow_builds_remote_via_helper() -> None:
    """Push step must build remote URL via build_wiki_remote_url (not inline GITHUB_TOKEN)."""
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "build_wiki_remote_url" in content
    assert "WIKI_TOKEN:" in content
    assert "WIKI_ACTOR:" in content
    assert "WIKI_REPOSITORY:" in content
