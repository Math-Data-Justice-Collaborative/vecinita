"""Gitleaks working-tree contract guards.

[Corpus: tests]
[Spec: docs/security/gitleaks-resolution.md]
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GITLEAKS_CONFIG = REPO_ROOT / ".gitleaks.toml"


def test_gitleaks_allowlists_gitignored_local_secret_files() -> None:
    """Local gitignored operator secret files should not fail --no-git scans."""
    text = GITLEAKS_CONFIG.read_text(encoding="utf-8")

    assert r"(?:^|/)\.env$" in text
    assert r"(?:^|/)\.env\.[^/]+$" in text
    assert r"(?:^|/)\.staging-supabase-keys\.local$" in text


def test_gitleaks_allowlists_local_security_tool_cache() -> None:
    """Local vendored security-tool assets should not create working-tree noise."""
    text = GITLEAKS_CONFIG.read_text(encoding="utf-8")

    assert r"(?:^|/)\.tools/security(?:/.*)?$" in text


def test_gitleaks_allowlists_generated_security_reports() -> None:
    """Generated secret-scan reports should not fail the next working-tree scan."""
    text = GITLEAKS_CONFIG.read_text(encoding="utf-8")

    assert r"(?:^|/)\.security-reports(?:/.*)?$" in text
