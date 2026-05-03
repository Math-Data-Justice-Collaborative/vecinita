#!/usr/bin/env python3
"""Validate that gateway install profile excludes scraper-only heavy dependencies.

Checks the backend pyproject base dependencies and agent optional dependencies to
ensure packages that can trigger Rust/source build paths are not required for
gateway operation.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[2]
_PY_GATEWAY = REPO_ROOT / "apis" / "gateway" / "pyproject.toml"
_PY_LEGACY = REPO_ROOT / "backend" / "pyproject.toml"
PYPROJECT = _PY_GATEWAY if _PY_GATEWAY.is_file() else _PY_LEGACY

FORBIDDEN = {
    "fastembed": "scraper-only embedding optimization can pull py-rust-stemmers",
    "py-rust-stemmers": "requires Rust toolchain when wheel is unavailable",
}


def _normalize_dep_name(dep_spec: str) -> str:
    head = dep_spec.split(";", 1)[0].strip()
    for sep in ("[", "<", ">", "=", "!", "~", " "):
        head = head.split(sep, 1)[0]
    return head.strip().lower().replace("_", "-")


def _read_deps() -> tuple[list[str], list[str]]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    base = data.get("project", {}).get("dependencies", [])
    optional = data.get("project", {}).get("optional-dependencies", {})
    agent = optional.get("agent", [])
    if not isinstance(base, list) or not isinstance(agent, list):
        raise ValueError("Unexpected pyproject dependency schema")
    return [str(x) for x in base], [str(x) for x in agent]


def main() -> int:
    if not PYPROJECT.exists():
        print(f"ERROR: pyproject not found: {PYPROJECT}", file=sys.stderr)
        return 1

    base_deps, agent_deps = _read_deps()
    check_specs = base_deps + agent_deps
    found: list[tuple[str, str]] = []

    for dep in check_specs:
        name = _normalize_dep_name(dep)
        if name in FORBIDDEN:
            found.append((name, dep))

    if found:
        print("Gateway dependency profile validation failed:", file=sys.stderr)
        for name, original in found:
            reason = FORBIDDEN.get(name, "forbidden package")
            print(f"- {original} -> {name}: {reason}", file=sys.stderr)
        return 1

    print("Gateway dependency profile OK: base+agent do not include forbidden scraper-only deps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
