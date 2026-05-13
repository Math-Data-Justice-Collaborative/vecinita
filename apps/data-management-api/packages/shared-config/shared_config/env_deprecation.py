"""Warn when legacy environment variable names are set (names only; no values)."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import yaml

_ALIASES_WARNED: set[tuple[str, str]] = set()


def _find_repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for p in [here.parent, *here.parents]:
        if (p / ".env.example").is_file() and (p / "config" / "env_aliases.example.yaml").is_file():
            return p
    return None


def _load_alias_rows(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "config" / "env_aliases.example.yaml"
    if not path.is_file():
        return []
    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = data.get("aliases") or []
    out: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        leg = row.get("legacy_env_name")
        can = row.get("canonical_env_name")
        if isinstance(leg, str) and isinstance(can, str) and leg and can:
            out.append({"legacy_env_name": leg, "canonical_env_name": can})
    return out


def warn_legacy_aliases(repo_root: Path | None = None) -> None:
    """Emit ``warnings.warn`` for each legacy env name that is set in ``os.environ``.

    Pydantic ``AliasChoices`` still resolves values; this surfaces the deprecation channel.
    """
    import os

    root = repo_root or _find_repo_root()
    if root is None:
        return
    for row in _load_alias_rows(root):
        legacy = row["legacy_env_name"]
        canonical = row["canonical_env_name"]
        if legacy not in os.environ:
            continue
        key = (legacy, canonical)
        if key in _ALIASES_WARNED:
            continue
        _ALIASES_WARNED.add(key)
        warnings.warn(
            f"Environment variable {legacy!r} is deprecated; use {canonical!r} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
