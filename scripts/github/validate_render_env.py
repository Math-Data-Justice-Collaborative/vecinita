#!/usr/bin/env python3
"""Validate the shared Render env contract.

Usage:
  python scripts/github/validate_render_env.py [path-to-env-file]

Defaults to `.env.prod.render` at the repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE_DIR = REPO_ROOT / "backend" / "src" / "utils"
if str(CONTRACT_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACT_MODULE_DIR))

from render_env_contract import parse_env_file, validate_shared_render_env


def _resolve_target(path: Path) -> tuple[Path | None, str | None]:
    if path.exists():
        return path, None

    example_path = path.with_suffix(path.suffix + ".example")
    if example_path.exists():
        return example_path, f"{path} not found; using template {example_path}"

    return None, None


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / ".env.prod.render"
    resolved_target, fallback_notice = _resolve_target(target)
    if resolved_target is None:
        print(f"WARNING: env file not found, skipping contract validation: {target}")
        return 0

    if fallback_notice:
        print(f"NOTICE: {fallback_notice}")

    env = parse_env_file(resolved_target)
    result = validate_shared_render_env(env)

    if result.warnings:
        print("Render env contract warnings:")
        for warning in result.warnings:
            print(f"- {warning}")

    if result.errors:
        print("Render env contract errors:")
        for error in result.errors:
            print(f"- {error}")
        return 1

    print(f"Render env contract OK: {resolved_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
