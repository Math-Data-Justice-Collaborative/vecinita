#!/usr/bin/env python3
"""Idempotent super-admin bootstrap for Supabase Auth (ADR-035 §9, RD-127)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import cast

from scripts.seed_first_admin import seed_super_admin


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed the canonical super-admin operator for RAG config promote.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print action without mutating Supabase"
    )
    args = parser.parse_args(argv)

    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    secret_key = os.environ.get("SUPABASE_SECRET_KEY", "").strip()
    email = os.environ.get("VECINITA_SUPER_ADMIN_EMAIL", "").strip()
    password = os.environ.get("SUPABASE_ADMIN_PASSWORD", "").strip()

    missing = [
        name
        for name, value in (
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_SECRET_KEY", secret_key),
            ("VECINITA_SUPER_ADMIN_EMAIL", email),
        )
        if not value
    ]
    if missing:
        print(f"Missing required env var(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    if not password and not args.dry_run:
        print("Missing required env var: SUPABASE_ADMIN_PASSWORD", file=sys.stderr)
        return 1

    action = seed_super_admin(
        supabase_url=supabase_url,
        secret_key=secret_key,
        email=email,
        password=password or "dry-run-placeholder",
        dry_run=cast("bool", args.dry_run),
    )
    print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
