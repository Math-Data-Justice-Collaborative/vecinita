#!/usr/bin/env python3
"""Validate key parity between production and staging Render env contract files.

This check ensures both files define the same key set, while allowing values to
intentionally differ across environments.

Usage:
  python scripts/github/validate_render_env_parity.py [prod-env-file] [staging-env-file]

Defaults:
  prod:    .env.prod.render
  staging: .env.staging.render
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_GATEWAY = REPO_ROOT / "apis" / "gateway"
_LEGACY = REPO_ROOT / "backend"
PY_ROOT = _GATEWAY if (_GATEWAY / "src").is_dir() else _LEGACY
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from src.utils.render_env_contract import parse_env_file  # noqa: E402


def _resolve_env_path(path: Path) -> tuple[Path | None, str | None]:
    if path.exists():
        return path, None

    example_path = path.with_suffix(path.suffix + ".example")
    if example_path.exists():
        return example_path, f"{path} not found; using template {example_path}"

    return None, None


def _load_env(path: Path) -> dict[str, str]:
    resolved_path, notice = _resolve_env_path(path)
    if resolved_path is None:
        raise FileNotFoundError(path)
    if notice:
        print(f"NOTICE: {notice}")
    return parse_env_file(resolved_path)


def main() -> int:
    prod_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / ".env.prod.render"
    staging_path = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / ".env.staging.render"
    )

    try:
        prod_env = _load_env(prod_path)
        staging_env = _load_env(staging_path)
    except FileNotFoundError as exc:
        print(f"Render env parity check failed: missing env file: {exc}")
        return 1

    prod_keys = set(prod_env.keys())
    staging_keys = set(staging_env.keys())

    missing_in_staging = sorted(prod_keys - staging_keys)
    missing_in_prod = sorted(staging_keys - prod_keys)

    if missing_in_staging or missing_in_prod:
        print("Render env parity errors:")
        if missing_in_staging:
            print("- Keys present in production but missing in staging:")
            for key in missing_in_staging:
                print(f"  - {key}")
        if missing_in_prod:
            print("- Keys present in staging but missing in production:")
            for key in missing_in_prod:
                print(f"  - {key}")
        return 1

    print(
        "Render env key parity OK: "
        f"{prod_path} <-> {staging_path} ({len(prod_keys)} keys)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
