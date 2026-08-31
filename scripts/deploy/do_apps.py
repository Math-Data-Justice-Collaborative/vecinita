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
STAGING_SPECS = [
    ROOT / "infra/do/staging/internal-write-api.yaml",
    ROOT / "infra/do/staging/chat-rag-backend.yaml",
    ROOT / "infra/do/staging/chat-rag-frontend.yaml",
    ROOT / "infra/do/staging/data-management-frontend.yaml",
]
PROD_APP_NAMES = [
    "vecinita-internal-write-api",
    "vecinita-chat-rag-backend",
    "vecinita-admin-frontend",
    "vecinita-chat-rag-frontend",
]
STAGING_APP_NAMES = [
    "vecinita-staging-write-api",
    "vecinita-staging-chat-api",
    "vecinita-staging-admin-fe",
    "vecinita-staging-chat-fe",
]

# Staging short names → same secret key sets as prod counterparts (F83).
_CHAT_BACKEND_NAMES = frozenset({"vecinita-chat-rag-backend", "vecinita-staging-chat-api"})
_WRITE_API_NAMES = frozenset({"vecinita-internal-write-api", "vecinita-staging-write-api"})
_CHAT_FE_NAMES = frozenset({"vecinita-chat-rag-frontend", "vecinita-staging-chat-fe"})
_ADMIN_FE_NAMES = frozenset({"vecinita-admin-frontend", "vecinita-staging-admin-fe"})


def specs_for_env(env: str) -> list[Path]:
    """Return App Platform YAML paths for ``prod`` or ``staging`` (ADR-054)."""
    if env == "prod":
        return list(DEFAULT_SPECS)
    if env == "staging":
        return list(STAGING_SPECS)
    msg = f"env must be 'prod' or 'staging' (got {env!r})"
    raise ValueError(msg)


def app_names_for_env(env: str) -> list[str]:
    """Return DO app ``name`` fields for ``prod`` or ``staging``."""
    if env == "prod":
        return list(PROD_APP_NAMES)
    if env == "staging":
        return list(STAGING_APP_NAMES)
    msg = f"env must be 'prod' or 'staging' (got {env!r})"
    raise ValueError(msg)


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


def cmd_create_all(client, *, env: str = "prod") -> int:
    rc = 0
    for path in specs_for_env(env):
        if not path.is_file():
            print(f"SKIP missing spec: {path}", file=sys.stderr)
            rc = 1
            continue
        print(f"==> [{env}] {path}")
        try:
            _ = cmd_create(client, path)
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
    if name in _CHAT_BACKEND_NAMES:
        _apply_env_from_os(
            spec,
            [
                "DATABASE_URL",
                "VECINITA_MODAL_EMBED_URL",
                "VECINITA_MODAL_LLM_URL",
                "VECINITA_MODAL_PROXY_KEY",  # RD-165 — required on /generate
                "VECINITA_MODAL_RERANK_URL",  # F45 — CE rerank when VECINITA_RAG_RERANK_CE=true
                "VECINITA_RAG_RERANK_CE",
                "VECINITA_RAG_QUERY_REFINE",
                "VECINITA_RAG_OUTPUT_VERIFY",
                "VECINITA_CORS_ORIGINS",
                "VECINITA_INTERNAL_WRITE_URL",
                "VECINITA_INTERNAL_API_KEY",
                "VECINITA_STATS_ENABLED",
            ],
        )
    elif name in _WRITE_API_NAMES:
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
                "VECINITA_MODAL_LLM_PLAYGROUND_URL",
                "VECINITA_CHAT_RAG_URL",
                "VECINITA_CHAT_FRONTEND_URL",
                "VECINITA_ADMIN_FRONTEND_URL",
                "VECINITA_HEALTH_TIMEOUT_MS",
                "VECINITA_AUDIT_RETENTION_DAYS",
                "SUPABASE_URL",
                "SUPABASE_SECRET_KEY",  # F69 — audit actor_email Admin lookup
                "VECINITA_AUTH_REQUIRED",
                "SUPABASE_JWT_AUD",
                # F78-F80 corpus automations / freshness / FT (EV-031)
                "VECINITA_AUTOMATIONS_ENABLED",
                "VECINITA_AUTOMATIONS_KILL_SWITCH",
                "VECINITA_AUTOMATIONS_MAX_CONCURRENT",
                "VECINITA_FRESHNESS_ENABLED",
                "VECINITA_FRESHNESS_STALE_DAYS",
                "VECINITA_FINETUNE_ENABLED",
                "VECINITA_FINETUNE_REQUIRE_APPROVE",
                "VECINITA_FINETUNE_MAX_CONCURRENT",
                "VECINITA_FINETUNE_MAX_RUNS_PER_DAY",
                "VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID",
                # F68 / #214 — optional feedback operator notify (Resend and/or webhook)
                "VECINITA_FEEDBACK_NOTIFY_EMAIL",
                "VECINITA_FEEDBACK_NOTIFY_WEBHOOK",
                "RESEND_API_KEY",
                "RESEND_SENDER_EMAIL",
            ],
        )
    elif name in _CHAT_FE_NAMES:
        _apply_env_from_os(spec, ["VITE_VECINITA_CHAT_API_URL"], scope="BUILD_TIME")
    elif name in _ADMIN_FE_NAMES:
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


def cmd_sync_all_secrets(client, *, env: str = "prod") -> int:
    """Push env vars from shell into all four Vecinita DO apps for ``env``."""
    names = app_names_for_env(env)
    rc = 0
    for name in names:
        print(f"==> sync-secrets [{env}] {name}")
        try:
            _ = cmd_sync_secrets(client, name)
        except SystemExit as exc:
            print(exc, file=sys.stderr)
            rc = 1
    return rc


def cmd_urls(client, *, env: str = "prod", include_frontends: bool = False) -> int:
    """Print smoke / connectivity env hints for the selected env's apps."""
    apps = _iter_apps(client)
    by_name = {(a.get("spec") or {}).get("name"): a for a in apps}
    if env == "staging":
        chat_key, write_key = "vecinita-staging-chat-api", "vecinita-staging-write-api"
        chat_fe_key, admin_fe_key = "vecinita-staging-chat-fe", "vecinita-staging-admin-fe"
        prefix = "VECINITA_STAGING"
    else:
        chat_key, write_key = "vecinita-chat-rag-backend", "vecinita-internal-write-api"
        chat_fe_key, admin_fe_key = "vecinita-chat-rag-frontend", "vecinita-admin-frontend"
        # Legacy export names still say STAGING for the sole/prod stack smoke scripts.
        prefix = "VECINITA_STAGING"
    chat = by_name.get(chat_key)
    write = by_name.get(write_key)
    chat_fe = by_name.get(chat_fe_key)
    admin_fe = by_name.get(admin_fe_key)
    found = False
    if chat:
        url = chat.get("default_ingress") or chat.get("live_url")
        if url:
            print(f"export {prefix}_CHAT_URL={url}")
            found = True
    if write:
        url = write.get("default_ingress") or write.get("live_url")
        if url:
            print(f"export {prefix}_WRITE_URL={url}")
            found = True
    if include_frontends:
        if chat_fe:
            url = chat_fe.get("default_ingress") or chat_fe.get("live_url")
            if url:
                print(f"export {prefix}_CHAT_FRONTEND_URL={url}")
                found = True
        if admin_fe:
            url = admin_fe.get("default_ingress") or admin_fe.get("live_url")
            if url:
                print(f"export {prefix}_ADMIN_FRONTEND_URL={url}")
                found = True
        modal_hint = (
            "https://vecinita-staging--vecinita-data-management-fastapi-app.modal.run"
            if env == "staging"
            else "https://vecinita--vecinita-data-management-fastapi-app.modal.run"
        )
        print(
            "# Modal admin API (set manually after modal deploy):",
            file=sys.stderr,
        )
        print(
            f"# export {prefix}_ADMIN_API_URL={modal_hint}",
            file=sys.stderr,
        )
    if not found:
        print(
            f"# No {env} vecinita apps found — run create-all --env {env} first.", file=sys.stderr
        )
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Vecinita DO App Platform (pydo)")
    sub = parser.add_subparsers(dest="command", required=True)
    _ = sub.add_parser("list", help="List all apps (id, name, phase, ingress)")
    p_create = sub.add_parser("create", help="Create app from YAML spec")
    _ = p_create.add_argument("--spec", type=Path, required=True)
    p_create_all = sub.add_parser(
        "create-all",
        help="Create all four apps for --env prod|staging (idempotent)",
    )
    _ = p_create_all.add_argument(
        "--env",
        choices=("prod", "staging"),
        default="prod",
        help="Target environment (default: prod = infra/do/*.yaml)",
    )
    p_dep = sub.add_parser("deploy", help="Trigger deployment for existing app by spec name")
    _ = p_dep.add_argument("--name", required=True, help="App spec name field")
    p_urls = sub.add_parser("urls", help="Print VECINITA_STAGING_* export lines")
    _ = p_urls.add_argument(
        "--env",
        choices=("prod", "staging"),
        default="prod",
        help="Which DO app set to print URLs for",
    )
    _ = p_urls.add_argument(
        "--frontend",
        action="store_true",
        help="Include VECINITA_STAGING_*_FRONTEND_URL for H4/H5 connectivity",
    )
    p_sync = sub.add_parser("sync-secrets", help="Update app spec env from shell")
    _ = p_sync.add_argument("--name", required=True, help="App spec name field")
    p_sync_all = sub.add_parser(
        "sync-all-secrets",
        help="Update all four apps for --env from shell env",
    )
    _ = p_sync_all.add_argument(
        "--env",
        choices=("prod", "staging"),
        default="prod",
        help="Target environment",
    )
    args = parser.parse_args()
    client = _client()
    if args.command == "list":
        return cmd_list(client)
    if args.command == "create":
        return cmd_create(client, args.spec)
    if args.command == "create-all":
        return cmd_create_all(client, env=args.env)
    if args.command == "deploy":
        return cmd_deploy(client, args.name)
    if args.command == "urls":
        return cmd_urls(
            client,
            env=args.env,
            include_frontends=getattr(args, "frontend", False),
        )
    if args.command == "sync-secrets":
        return cmd_sync_secrets(client, args.name)
    if args.command == "sync-all-secrets":
        return cmd_sync_all_secrets(client, env=args.env)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
