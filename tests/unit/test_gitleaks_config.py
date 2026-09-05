"""Working-tree gitleaks allowlist contract (QA-005)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / ".gitleaks.toml"


def test_gitleaks_allowlists_local_runtime_secret_files() -> None:
    """Common local secret stores should not fail current-tree scans."""
    text = CONFIG.read_text(encoding="utf-8")
    for pattern in (
        r"""(?:^|/)\.env$""",
        r"""(?:^|/)\.env\.staging$""",
        r"""(?:^|/)\.staging-supabase-keys\.local$""",
    ):
        assert pattern in text


def test_gitleaks_allowlists_generated_security_artifacts() -> None:
    """Generated local security outputs/vendor assets should not fail working-tree scans."""
    text = CONFIG.read_text(encoding="utf-8")
    for pattern in (
        r"""(?:^|/)\.security-reports(?:/.*)?$""",
        r"""(?:^|/)\.tools/security/assets(?:/.*)?$""",
    ):
        assert pattern in text
