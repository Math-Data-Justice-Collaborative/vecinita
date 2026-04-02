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
BACKEND_SRC = REPO_ROOT / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from src.utils.render_env_contract import parse_env_file, validate_shared_render_env


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / ".env.prod.render"
    if not target.exists():
        print(f"ERROR: env file not found: {target}")
        return 2

    env = parse_env_file(target)
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

    print(f"Render env contract OK: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
