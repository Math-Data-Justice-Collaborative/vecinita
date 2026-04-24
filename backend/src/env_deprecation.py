"""Bootstrap legacy → canonical env names (copy + warn; names only in messages)."""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

import yaml

_COPIED_OR_WARNED: set[tuple[str, str]] = set()


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


def apply_legacy_aliases_and_warn(repo_root: Path | None = None) -> None:
    """If a legacy key is set and canonical is unset, copy value to canonical; always warn once per pair."""
    root = repo_root or _find_repo_root()
    if root is None:
        return
    for row in _load_alias_rows(root):
        legacy = row["legacy_env_name"]
        canonical = row["canonical_env_name"]
        if legacy not in os.environ:
            continue
        leg_val = os.environ.get(legacy, "")
        if not os.getenv(canonical) and leg_val:
            os.environ.setdefault(canonical, leg_val)
        pair = (legacy, canonical)
        if pair in _COPIED_OR_WARNED:
            continue
        _COPIED_OR_WARNED.add(pair)
        warnings.warn(
            f"Environment variable {legacy!r} is deprecated; prefer {canonical!r}.",
            DeprecationWarning,
            stacklevel=2,
        )
