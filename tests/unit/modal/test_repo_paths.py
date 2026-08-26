"""Unit tests for shared Modal repo path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest
from infra.modal import repo_paths
from infra.modal.repo_paths import MODAL_PKG_ROOT, MODAL_ROOT_MOUNT, resolve_repo_root


def test_resolve_repo_root_from_infra_modal_module() -> None:
    """resolve_repo_root returns repo root when called from infra/modal/*.py."""
    repo_root = resolve_repo_root()
    assert repo_root.name == "vecinita"
    assert (repo_root / "infra" / "modal" / "repo_paths.py").is_file()


def test_resolve_repo_root_uses_fallback_outside_repo_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """resolve_repo_root falls back when repo_paths is not under infra/modal."""
    fallback = Path("/opt/modal-fallback-test")
    monkeypatch.setattr(repo_paths, "__file__", "/var/task/single_file.py")
    assert repo_paths.resolve_repo_root(fallback=fallback) == fallback


def test_modal_mount_constants() -> None:
    """Shared mount roots match Modal image conventions."""
    assert Path("/opt/vecinita") == MODAL_PKG_ROOT
    assert Path("/root") == MODAL_ROOT_MOUNT
