"""BUG-2026-07-05: DO frontend deploys must not fail on root husky prepare (Playground missing on prod)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DO_FRONTEND_SPECS = (
    REPO_ROOT / "infra/do/data-management-frontend.yaml",
    REPO_ROOT / "infra/do/chat-rag-frontend.yaml",
)


def test_do_frontend_build_commands_disable_husky() -> None:
    """DO npm ci must set HUSKY=0 — S008 root prepare runs husky and breaks App Platform builds."""
    for spec_path in DO_FRONTEND_SPECS:
        content = spec_path.read_text(encoding="utf-8")
        assert "build_command: HUSKY=0 npm ci && npm run build" in content, (
            f"{spec_path.name} must set HUSKY=0 in build_command"
        )


def test_root_prepare_script_skips_husky_when_disabled() -> None:
    """Root prepare must not invoke bare husky without a guard (DO has no husky on PATH)."""
    content = (REPO_ROOT / "package.json").read_text(encoding="utf-8")
    assert '"prepare": "husky"' not in content
    assert "prepare-husky.mjs" in content
