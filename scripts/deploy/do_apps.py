#!/usr/bin/env python3
"""DigitalOcean App Platform deploy helper via pydo (replaces doctl for CI/agents).

Requires: DIGITALOCEAN_TOKEN (read/write Apps scope).

Examples:
  uv run --with pydo --with pyyaml scripts/deploy/do_apps.py list
  uv run --with pydo --with pyyaml scripts/deploy/do_apps.py create --spec infra/do/internal-write-api.yaml
  uv run --with pydo --with pyyaml scripts/deploy/do_apps.py create-all
  uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-chat-rag-backend
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from deploy.modal_url_validate import validate_modal_service_url  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPECS = [
    ROOT / "infra/do/internal-write-api.yaml",
    ROOT / "infra/do/chat-rag-backend.yaml",
    ROOT / "infra/do/chat-rag-frontend.yaml",
    ROOT / "infra/do/data-management-frontend.yaml",
]


def _client():
    try:
        from pydo import Client
    except ImportError as exc:
        raise SystemExit(
            "pydo not installed. Run: uv run --with pydo --with pyyaml scripts/deploy/do_apps.py ..."
        ) from exc
    token = os.environ.get("DIGITALOCEAN_TOKEN", "").strip()
    if not token:
        raise SystemExit("DIGITALOCEAN_TOKEN is unset. Create a DO API token with Apps read/write.")
    return Client(token=token)


def _load_spec(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid app spec (expected mapping): {path}")
    if "name" not in data:
        raise SystemExit(f"App spec missing 'name': {path}")
    return data


def _iter_apps(client) -> list[dict[str, Any]]:
    apps: list[dict[str, Any]] = []
    page = 1
    while True:
        resp = client.apps.list(page=page, per_page=200)
        apps.extend(resp.get("apps") or [])
        pages = (resp.get("links") or {}).get("pages") or {}
        nxt = pages.get("next")
        if not nxt:
            break
        parsed = urlparse(nxt)
        page = int(parse_qs(parsed.query)["page"][0])
    return apps


def _find_app(apps: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for app in apps:
        spec = app.get("spec") or {}
        if spec.get("name") == name:
            return app
    return None


def cmd_list(client) -> int:
    apps = _iter_apps(client)
    if not apps:
        print("No App Platform apps found.")
        return 0
    for app in apps:
        spec = app.get("spec") or {}
        ingress = app.get("default_ingress") or app.get("live_url") or "—"
        phase = ((app.get("active_deployment") or {}).get("phase")) or "—"
        print(f"{app.get('id')}\t{spec.get('name')}\t{phase}\t{ingress}")
    return 0


def cmd_create(client, spec_path: Path) -> int:
    spec = _load_spec(spec_path)
    name = spec["name"]
    apps = _iter_apps(client)
    existing = _find_app(apps, name)
    if existing:
        print(f"App already exists: {name} ({existing['id']}) — use deploy/update instead.")
        return 0
    resp = client.apps.create(body={"spec": spec})
    app = resp.get("app") or {}
    print(f"Created {name}: id={app.get('id')} ingress={app.get('default_ingress', '—')}")
    return 0


def cmd_create_all(client) -> int:
    rc = 0
    for path in DEFAULT_SPECS:
        if not path.is_file():
            print(f"SKIP missing spec: {path}", file=sys.stderr)
            rc = 1
            continue
        print(f"==> {path.name}")
        try:
            cmd_create(client, path)
        except SystemExit as exc:
            print(exc, file=sys.stderr)
            rc = 1
    return rc


def cmd_deploy(client, name: str) -> int:
    apps = _iter_apps(client)
    app = _find_app(apps, name)
    if not app:
        raise SystemExit(f"No app named {name!r}. Run create or create-all first.")
    app_id = app["id"]
    resp = client.apps.create_deployment(app_id=app_id, body={"force_build": True})
    dep = resp.get("deployment") or {}
    print(f"Deployment started for {name}: deployment_id={dep.get('id')} phase={dep.get('phase')}")
    return 0


def _apply_env_from_os(spec: dict[str, Any], keys: list[str], scope: str = "RUN_TIME") -> None:
    for key in keys:
        val = os.environ.get(key, "").strip()
        if not val:
            continue
        try:
            validate_modal_service_url(key, val)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        for section in ("services", "static_sites", "workers", "jobs"):
            for comp in spec.get(section) or []:
                envs = comp.setdefault("envs", [])
                for env in envs:
                    if env.get("key") == key:
                        env["value"] = val
                        env["type"] = env.get("type", "SECRET")
                        env["scope"] = env.get("scope", scope)
                        break
                else:
                    envs.append(
                        {
                            "key": key,
                            "value": val,
                            "scope": scope,
                            "type": "SECRET",
                        }
                    )


def cmd_sync_secrets(client, name: str) -> int:
    """Push env vars from shell into the live app spec via apps.update.

    Reads the LIVE spec (not the YAML file) to preserve existing encrypted
    secrets.  Only env vars present in the current shell are overwritten;
    encrypted ``EV[...]`` values for other keys remain untouched.
    """
    apps = _iter_apps(client)
    app = _find_app(apps, name)
    if not app:
        raise SystemExit(f"No app named {name!r}")
    spec = app.get("spec") or {}
    if name == "vecinita-chat-rag-backend":
        _apply_env_from_os(
            spec,
            [
                "DATABASE_URL",
                "VECINITA_MODAL_EMBED_URL",
                "VECINITA_MODAL_LLM_URL",
                "VECINITA_CORS_ORIGINS",
                "VECINITA_INTERNAL_WRITE_URL",
                "VECINITA_INTERNAL_API_KEY",
                "VECINITA_STATS_ENABLED",
            ],
        )
    elif name == "vecinita-internal-write-api":
        _apply_env_from_os(
            spec,
            [
                "DATABASE_URL",
                "VECINITA_INTERNAL_API_KEY",
                "VECINITA_CORS_ORIGINS",
                "VECINITA_MODAL_DATA_MGMT_URL",
                "VECINITA_MODAL_PROXY_KEY",
                "VECINITA_MODAL_EMBED_URL",
                "VECINITA_MODAL_LLM_URL",
                "VECINITA_MODAL_OLLAMA_URL",
                "VECINITA_CHAT_RAG_URL",
                "VECINITA_CHAT_FRONTEND_URL",
                "VECINITA_ADMIN_FRONTEND_URL",
                "VECINITA_HEALTH_TIMEOUT_MS",
                "VECINITA_AUDIT_RETENTION_DAYS",
                "SUPABASE_URL",
                "VECINITA_AUTH_REQUIRED",
                "SUPABASE_JWT_AUD",
            ],
        )
    elif name == "vecinita-chat-rag-frontend":
        _apply_env_from_os(spec, ["VITE_VECINITA_CHAT_API_URL"], scope="BUILD_TIME")
    elif name == "vecinita-admin-frontend":
        _apply_env_from_os(
            spec,
            [
                "VITE_VECINITA_ADMIN_API_URL",
                "VITE_VECINITA_MODAL_PROXY_KEY",
                "VITE_VECINITA_CORPUS_API_URL",
                "VITE_VECINITA_CORPUS_API_KEY",
                "VITE_SUPABASE_URL",
                "VITE_SUPABASE_PUBLISHABLE_KEY",
            ],
            scope="BUILD_TIME",
        )
    app_id = app["id"]
    client.apps.update(id=app_id, body={"spec": spec})
    print(f"Updated secrets for {name} ({app_id})")
    return 0


def cmd_sync_all_secrets(client) -> int:
    """Push env vars from shell into all four Vecinita DO apps."""
    names = [
        "vecinita-internal-write-api",
        "vecinita-chat-rag-backend",
        "vecinita-admin-frontend",
        "vecinita-chat-rag-frontend",
    ]
    rc = 0
    for name in names:
        print(f"==> sync-secrets {name}")
        try:
            cmd_sync_secrets(client, name)
        except SystemExit as exc:
            print(exc, file=sys.stderr)
            rc = 1
    return rc


def cmd_urls(client, *, include_frontends: bool = False) -> int:
    """Print staging smoke / connectivity env hints for vecinita-* apps."""
    apps = _iter_apps(client)
    by_name = {(a.get("spec") or {}).get("name"): a for a in apps}
    chat = by_name.get("vecinita-chat-rag-backend")
    write = by_name.get("vecinita-internal-write-api")
    chat_fe = by_name.get("vecinita-chat-rag-frontend")
    admin_fe = by_name.get("vecinita-admin-frontend")
    found = False
    if chat:
        url = chat.get("default_ingress") or chat.get("live_url")
        if url:
            print(f"export VECINITA_STAGING_CHAT_URL={url}")
            found = True
    if write:
        url = write.get("default_ingress") or write.get("live_url")
        if url:
            print(f"export VECINITA_STAGING_WRITE_URL={url}")
            found = True
    if include_frontends:
        if chat_fe:
            url = chat_fe.get("default_ingress") or chat_fe.get("live_url")
            if url:
                print(f"export VECINITA_STAGING_CHAT_FRONTEND_URL={url}")
                found = True
        if admin_fe:
            url = admin_fe.get("default_ingress") or admin_fe.get("live_url")
            if url:
                print(f"export VECINITA_STAGING_ADMIN_FRONTEND_URL={url}")
                found = True
        print(
            "# Modal admin API (set manually after modal deploy):",
            file=sys.stderr,
        )
        print(
            "# export VECINITA_STAGING_ADMIN_API_URL=https://vecinita--vecinita-data-management-fastapi-app.modal.run",
            file=sys.stderr,
        )
    if not found:
        print("# No vecinita apps found — run create-all first.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Vecinita DO App Platform (pydo)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List all apps (id, name, phase, ingress)")
    p_create = sub.add_parser("create", help="Create app from YAML spec")
    p_create.add_argument("--spec", type=Path, required=True)
    sub.add_parser("create-all", help="Create all four infra/do/*.yaml apps (idempotent)")
    p_dep = sub.add_parser("deploy", help="Trigger deployment for existing app by spec name")
    p_dep.add_argument("--name", required=True, help="App spec name field")
    p_urls = sub.add_parser("urls", help="Print VECINITA_STAGING_* export lines")
    p_urls.add_argument(
        "--frontend",
        action="store_true",
        help="Include VECINITA_STAGING_*_FRONTEND_URL for H4/H5 connectivity",
    )
    p_sync = sub.add_parser("sync-secrets", help="Update app spec env from shell")
    p_sync.add_argument("--name", required=True, help="App spec name field")
    sub.add_parser(
        "sync-all-secrets",
        help="Update all four Vecinita DO apps from shell env (see infra/do/.env.example)",
    )
    args = parser.parse_args()
    client = _client()
    if args.command == "list":
        return cmd_list(client)
    if args.command == "create":
        return cmd_create(client, args.spec)
    if args.command == "create-all":
        return cmd_create_all(client)
    if args.command == "deploy":
        return cmd_deploy(client, args.name)
    if args.command == "urls":
        return cmd_urls(client, include_frontends=getattr(args, "frontend", False))
    if args.command == "sync-secrets":
        return cmd_sync_secrets(client, args.name)
    if args.command == "sync-all-secrets":
        return cmd_sync_all_secrets(client)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
