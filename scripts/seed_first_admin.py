#!/usr/bin/env python3
"""Idempotent first-admin bootstrap for Supabase Auth (ADR-027 §8, TP-S004-10)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import cast

import httpx

_DEFAULT_ROLE = "admin"


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        msg = f"Missing required env var: {name}"
        raise RuntimeError(msg)
    return value


def _admin_headers(secret_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {secret_key}",
        "apikey": secret_key,
        "Content-Type": "application/json",
    }


def _find_user_id_by_email(client: httpx.Client, email: str) -> str | None:
    page = 1
    while True:
        response = client.get(
            "/auth/v1/admin/users",
            params={"page": page, "per_page": 200},
        )
        if response.status_code != 200:
            msg = f"Supabase list users failed: HTTP {response.status_code}"
            raise RuntimeError(msg)
        body = response.json()
        if not isinstance(body, dict):
            return None
        users = body.get("users")
        if not isinstance(users, list) or not users:
            return None
        for raw_user in users:
            if not isinstance(raw_user, dict):
                continue
            if raw_user.get("email") == email:
                user_id = raw_user.get("id")
                if isinstance(user_id, str):
                    return user_id
        if len(users) < 200:
            return None
        page += 1


def _require_ok(response: httpx.Response, *, context: str) -> None:
    if response.status_code >= 400:
        msg = f"{context}: HTTP {response.status_code}"
        raise RuntimeError(msg)


def _ensure_admin_role(client: httpx.Client, user_id: str) -> None:
    response = client.put(
        f"/auth/v1/admin/users/{user_id}",
        json={"app_metadata": {"role": _DEFAULT_ROLE}},
    )
    _require_ok(response, context="update admin role")


def seed_first_admin(
    *,
    supabase_url: str,
    secret_key: str,
    email: str,
    password: str,
    dry_run: bool = False,
) -> str:
    """Create or update the first admin. Returns action taken."""
    base = supabase_url.rstrip("/")
    with httpx.Client(base_url=base, headers=_admin_headers(secret_key), timeout=30.0) as client:
        existing_id = _find_user_id_by_email(client, email)
        if existing_id is not None:
            if dry_run:
                return f"would_update_role:{existing_id}"
            _ensure_admin_role(client, existing_id)
            return f"updated_role:{existing_id}"

        if dry_run:
            return "would_create_admin"

        create = client.post(
            "/auth/v1/admin/users",
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
                "app_metadata": {"role": _DEFAULT_ROLE},
            },
        )
        if create.status_code == 422:
            # Race or duplicate — re-fetch and patch role
            existing_id = _find_user_id_by_email(client, email)
            if existing_id is None:
                _require_ok(create, context="create admin user")
            _ensure_admin_role(client, existing_id)
            return f"updated_role:{existing_id}"

        _require_ok(create, context="create admin user")
        created = create.json()
        if isinstance(created, dict):
            user = created.get("user")
            if isinstance(user, dict):
                user_id = user.get("id")
                if isinstance(user_id, str):
                    return f"created:{user_id}"
        return "created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the first Supabase admin operator.")
    parser.add_argument("--dry-run", action="store_true", help="Print action without mutating Supabase")
    args = parser.parse_args(argv)

    try:
        supabase_url = _required_env("SUPABASE_URL")
        secret_key = _required_env("SUPABASE_SECRET_KEY")
        email = _required_env("SUPABASE_ADMIN_EMAIL")
        password = _required_env("SUPABASE_ADMIN_PASSWORD")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not password and not args.dry_run:
        print("Missing required env var: SUPABASE_ADMIN_PASSWORD", file=sys.stderr)
        return 1

    action = seed_first_admin(
        supabase_url=supabase_url,
        secret_key=secret_key,
        email=email,
        password=password or "dry-run-placeholder",
        dry_run=cast(bool, args.dry_run),
    )
    print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
