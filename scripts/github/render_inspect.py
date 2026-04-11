#!/usr/bin/env python3
"""Inspect Render deploys, logs, and service env metadata via the Render REST API.

Requires RENDER_API_KEY (https://dashboard.render.com/api-keys).

API reference:
  https://api-docs.render.com/reference/list-deploys
  https://api-docs.render.com/reference/retrieve-deploy
  https://api-docs.render.com/reference/retrieve-service
  https://api-docs.render.com/reference/list-logs

Examples:
  python3 scripts/github/render_inspect.py deploys --service-id srv-abc123
  python3 scripts/github/render_inspect.py deploy --service-id srv-abc123 --deploy-id dep-xyz
  python3 scripts/github/render_inspect.py env --service-id srv-abc123
  python3 scripts/github/render_inspect.py logs --service-id srv-abc123 --type build --limit 50
  python3 scripts/github/render_inspect.py services --limit 50
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


RENDER_API_BASE = "https://api.render.com/v1"


def _api_key() -> str:
    key = os.environ.get("RENDER_API_KEY", "").strip()
    if not key:
        print("error: set RENDER_API_KEY (https://dashboard.render.com/api-keys)", file=sys.stderr)
        sys.exit(1)
    return key


def _get(url: str, api_key: str) -> dict | list:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _service_body(raw: dict) -> dict:
    if isinstance(raw, dict) and isinstance(raw.get("service"), dict):
        return raw["service"]
    return raw


def _deploy_body(item: dict) -> dict:
    if isinstance(item, dict) and isinstance(item.get("deploy"), dict):
        return item["deploy"]
    return item


def cmd_deploys(args: argparse.Namespace) -> int:
    api_key = _api_key()
    limit = max(1, min(100, args.limit))
    url = f"{RENDER_API_BASE}/services/{args.service_id}/deploys?limit={limit}"
    try:
        data = _get(url, api_key)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    items = data
    if isinstance(data, dict) and isinstance(data.get("deploys"), list):
        items = data["deploys"]
    if not isinstance(items, list):
        print(json.dumps(data, indent=2)[:8000])
        return 0
    rows: list[tuple[str, str, str, str]] = []
    for item in items:
        d = _deploy_body(item) if isinstance(item, dict) else {}
        did = d.get("id", "?")
        st = d.get("status", "?")
        created = d.get("createdAt", "")[:19].replace("T", " ")
        commit = (d.get("commit") or {}) if isinstance(d.get("commit"), dict) else {}
        msg = (commit.get("message") or "")[:50].replace("\n", " ")
        rows.append((str(did), str(st), created, msg))
    w = max(len(r[0]) for r in rows) if rows else 10
    for did, st, created, msg in rows:
        print(f"{did:{w}}  {st:12}  {created}  {msg}")
    return 0


def cmd_deploy(args: argparse.Namespace) -> int:
    api_key = _api_key()
    url = f"{RENDER_API_BASE}/services/{args.service_id}/deploys/{args.deploy_id}"
    try:
        data = _get(url, api_key)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    d = _deploy_body(data) if isinstance(data, dict) else data
    print(json.dumps(d, indent=2, default=str))
    return 0


def _env_var_summary(entry: dict) -> tuple[str, str, str]:
    key = str(entry.get("key", ""))
    if entry.get("fromDatabase"):
        return key, "fromDatabase", json.dumps(entry["fromDatabase"], sort_keys=True)
    if entry.get("fromService"):
        return key, "fromService", json.dumps(entry["fromService"], sort_keys=True)
    if entry.get("fromGroup"):
        return key, "fromGroup", str(entry.get("fromGroup"))
    if entry.get("generateValue"):
        return key, "generateValue", "true"
    if entry.get("sync") is False:
        return key, "sync_false", "(dashboard / env group; not overwritten by blueprint)"
    val = entry.get("value")
    if val is None or val == "":
        return key, "empty", ""
    s = str(val)
    if len(s) > 48:
        s = s[:24] + "…" + s[-12:]
    return key, "value", s


def cmd_env(args: argparse.Namespace) -> int:
    api_key = _api_key()
    url = f"{RENDER_API_BASE}/services/{args.service_id}"
    try:
        raw = _get(url, api_key)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    svc = _service_body(raw)
    name = svc.get("name", "")
    print(f"service: {name} ({args.service_id})")
    env_vars = svc.get("envVars") or []
    if not isinstance(env_vars, list):
        print("no envVars in response", file=sys.stderr)
        return 1
    for entry in sorted(env_vars, key=lambda x: str(x.get("key", ""))):
        if not isinstance(entry, dict):
            continue
        k, kind, preview = _env_var_summary(entry)
        if not k:
            continue
        print(f"{k:48}  {kind:14}  {preview}")
    print(
        "\nnote: Render does not return secret values via API; use the dashboard to rotate or verify.",
        file=sys.stderr,
    )
    return 0


def _owner_id(service: dict, raw: dict) -> str | None:
    for path in (
        service.get("ownerId"),
        service.get("owner", {}).get("id") if isinstance(service.get("owner"), dict) else None,
        raw.get("ownerId"),
    ):
        if path and isinstance(path, str) and len(path) > 2:
            return path
    return None


def cmd_logs(args: argparse.Namespace) -> int:
    api_key = _api_key()
    svc_url = f"{RENDER_API_BASE}/services/{args.service_id}"
    try:
        raw = _get(svc_url, api_key)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    svc = _service_body(raw)
    owner = _owner_id(svc, raw if isinstance(raw, dict) else {})
    if not owner:
        print(
            "error: could not determine workspace ownerId from service payload; "
            "use Render Dashboard logs or `render logs -r SERVICE_ID -o text` after `render login`.",
            file=sys.stderr,
        )
        return 1

    params: list[tuple[str, str]] = [
        ("ownerId", owner),
        ("limit", str(max(1, min(100, args.limit)))),
        ("direction", "backward"),
        ("resource", args.service_id),
    ]
    for t in args.type or []:
        params.append(("type", t))
    qs = urllib.parse.urlencode(params)
    url = f"{RENDER_API_BASE}/logs?{qs}"
    try:
        data = _get(url, api_key)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print(json.dumps(data, indent=2)[:8000])
        return 0
    logs = data.get("logs") or []
    for row in logs:
        if not isinstance(row, dict):
            continue
        ts = str(row.get("timestamp", ""))[:22]
        msg = row.get("message", "")
        print(f"{ts}  {msg}")
    if data.get("hasMore"):
        print("\n(has more — increase --limit or narrow time window)", file=sys.stderr)
    return 0


def cmd_services(args: argparse.Namespace) -> int:
    api_key = _api_key()
    limit = max(1, min(100, args.limit))
    url = f"{RENDER_API_BASE}/services?limit={limit}"
    try:
        data = _get(url, api_key)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    if not isinstance(data, list):
        print(json.dumps(data, indent=2)[:8000])
        return 0
    for item in data:
        if not isinstance(item, dict):
            continue
        s = _service_body(item)
        sid = s.get("id", "")
        name = s.get("name", "")
        st = s.get("suspended", "")
        print(f"{sid}\t{name}\tsuspended={st}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Render API inspect (deploys, env, logs).")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_dep = sub.add_parser("deploys", help="List recent deploys for a service")
    p_dep.add_argument("--service-id", required=True, help="Render service id, e.g. srv-…")
    p_dep.add_argument("--limit", type=int, default=15, help="Max deploys (1–100, default 15)")
    p_dep.set_defaults(func=cmd_deploys)

    p_one = sub.add_parser("deploy", help="Show one deploy JSON")
    p_one.add_argument("--service-id", required=True)
    p_one.add_argument("--deploy-id", required=True, help="Deploy id, e.g. dep-…")
    p_one.set_defaults(func=cmd_deploy)

    p_env = sub.add_parser("env", help="List env var keys and binding kinds (no secret values)")
    p_env.add_argument("--service-id", required=True)
    p_env.set_defaults(func=cmd_env)

    p_logs = sub.add_parser("logs", help="Fetch recent logs (ownerId from service; use --type build for build logs)")
    p_logs.add_argument("--service-id", required=True)
    p_logs.add_argument(
        "--type",
        action="append",
        default=[],
        metavar="TYPE",
        help="Log type filter (repeatable): app, build, request (default: all types if omitted)",
    )
    p_logs.add_argument("--limit", type=int, default=80, help="Max log lines (1–100, default 80)")
    p_logs.set_defaults(func=cmd_logs)

    p_sv = sub.add_parser("services", help="List services visible to this API key")
    p_sv.add_argument("--limit", type=int, default=50, help="Max services (default 50)")
    p_sv.set_defaults(func=cmd_services)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
