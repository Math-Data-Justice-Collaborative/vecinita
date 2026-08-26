"""Shared Modal deploy path helpers (infra/modal apps)."""

from __future__ import annotations

from pathlib import Path

MODAL_PKG_ROOT = Path("/opt/vecinita")
MODAL_ROOT_MOUNT = Path("/root")


def resolve_repo_root(fallback: Path = MODAL_PKG_ROOT) -> Path:
    """Repo root when deploying from ``infra/modal``; ``fallback`` when Modal mounts the app module."""
    here = Path(__file__).resolve()
    if here.parent.name == "modal" and here.parent.parent.name == "infra":
        return here.parents[2]
    return fallback
