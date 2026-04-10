#!/usr/bin/env python3
"""Sync dotenv-style files to GitHub Actions secrets (gh) or Render service env (REST API).

  # Dry-run: list RENDER_* keys that would be pushed from merged local env files
  python3 scripts/env_sync.py gh --file .env --file .env.prod.render --prefix RENDER_ --dry-run

  # Apply to repo secrets (requires: gh auth login)
  python3 scripts/env_sync.py gh --file .env --prefix RENDER_ --yes

  # Staging / production environment secrets in GitHub
  python3 scripts/env_sync.py gh --file .env --prefix RENDER_ --environment staging --yes

  # Patch a Render web service env vars from .env.prod.render (requires RENDER_API_KEY)
  python3 scripts/env_sync.py render-api --file .env.prod.render --service-id srv-xxxxx --dry-run
  python3 scripts/env_sync.py render-api --file .env.prod.render --service-id srv-xxxxx --yes

  # List Render services (CLI JSON output)
  python3 scripts/env_sync.py render-list

Do not commit real .env files. Values are never printed except key names in --dry-run.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


def parse_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        env[key] = value
    return env


def merge_files(paths: list[Path]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for p in paths:
        if not p.is_file():
            print(f"warning: skip missing file {p}", file=sys.stderr)
            continue
        merged.update(parse_dotenv(p))
    return merged


def filter_keys(
    data: dict[str, str],
    prefix: str | None,
    keys_only: set[str] | None,
    *,
    all_keys: bool = False,
) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in data.items():
        if not v:
            continue
        if keys_only is not None:
            if k not in keys_only:
                continue
        elif not all_keys and prefix is not None and not k.startswith(prefix):
            continue
        out[k] = v
    return out


def cmd_gh(args: argparse.Namespace) -> int:
    paths = [Path(p).resolve() for p in args.file]
    data = merge_files(paths)
    subset = filter_keys(
        data,
        args.prefix,
        set(args.key) if args.key else None,
        all_keys=args.all_keys,
    )
    if not subset:
        print("No non-empty keys matched filters.", file=sys.stderr)
        return 1

    env_name = args.environment
    repo_args: list[str] = []
    if args.repo:
        repo_args.extend(["--repo", args.repo])

    if args.dry_run:
        print("Would set GitHub Actions secrets:")
        for k in sorted(subset):
            print(f"  {k}")
        if env_name:
            print(f"  (GitHub environment: {env_name})")
        return 0

    if not args.yes:
        print("Refusing to write secrets without --yes", file=sys.stderr)
        return 1

    for key, value in sorted(subset.items()):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write(value)
            tmp_path = tmp.name
        try:
            cmd = ["gh", "secret", "set", key, *repo_args]
            if env_name:
                cmd.extend(["--env", env_name])
            cmd.extend(["--body-file", tmp_path])
            r = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"error: gh secret set {key} failed: {r.stderr or r.stdout}", file=sys.stderr)
                return r.returncode
            print(f"ok: {key}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return 0


def cmd_render_api(args: argparse.Namespace) -> int:
    api_key = os.environ.get("RENDER_API_KEY", "").strip()
    if not api_key and not args.dry_run:
        print("error: set RENDER_API_KEY in the environment", file=sys.stderr)
        return 1

    paths = [Path(p).resolve() for p in args.file]
    data = merge_files(paths)
    subset = filter_keys(
        data,
        args.prefix,
        set(args.key) if args.key else None,
        all_keys=args.all_keys,
    )
    if not subset:
        print("No non-empty keys matched filters.", file=sys.stderr)
        return 1

    payload = {"envVars": [{"key": k, "value": v} for k, v in sorted(subset.items())]}
    body = json.dumps(payload).encode("utf-8")

    if args.dry_run:
        print(f"Would PATCH https://api.render.com/v1/services/{args.service_id}")
        print(f"  with {len(subset)} env vars (keys only): {', '.join(sorted(subset))}")
        return 0

    if not args.yes:
        print("Refusing to call Render API without --yes", file=sys.stderr)
        return 1

    url = f"https://api.render.com/v1/services/{args.service_id}"
    req = urllib.request.Request(
        url,
        data=body,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"error: Render API HTTP {e.code}: {err}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print("ok: Render service updated (may trigger redeploy).")
    if args.verbose and raw:
        print(raw[:2000])
    return 0


def cmd_render_list(_args: argparse.Namespace) -> int:
    r = subprocess.run(
        ["render", "services", "-o", "json"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        return r.returncode
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        print(r.stdout)
        return 0
    if isinstance(data, list):
        for svc in data:
            if not isinstance(svc, dict):
                continue
            sid = svc.get("id", "")
            name = svc.get("name", "")
            stype = svc.get("type", svc.get("serviceType", ""))
            print(f"{sid}\t{name}\t{stype}")
    else:
        print(json.dumps(data, indent=2)[:4000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    gh = sub.add_parser("gh", help="Push secrets with gh secret set")
    gh.add_argument("--file", action="append", required=True, help="Dotenv file (repeat to merge, later wins)")
    gh.add_argument("--prefix", default="RENDER_", help="Only keys starting with this prefix (default: RENDER_)")
    gh.add_argument("--key", action="append", help="Exact key name (repeat); overrides --prefix if set")
    gh.add_argument("--repo", help="owner/repo (default: current gh repo)")
    gh.add_argument("--environment", "-e", metavar="NAME", help="GitHub environment (staging / production)")
    gh.add_argument("--dry-run", action="store_true")
    gh.add_argument("--yes", action="store_true", help="Confirm write")
    gh.add_argument(
        "--all-keys",
        action="store_true",
        help="Sync every non-empty key (ignores --prefix). Use with care.",
    )
    gh.set_defaults(func=cmd_gh)

    ra = sub.add_parser("render-api", help="PATCH Render service envVars via REST API")
    ra.add_argument("--file", action="append", required=True, help="Dotenv file (repeat to merge)")
    ra.add_argument("--service-id", required=True, help="Render service id srv-...")
    ra.add_argument("--prefix", default=None, help="Only keys with this prefix (optional)")
    ra.add_argument("--key", action="append", help="Exact key (repeat)")
    ra.add_argument("--dry-run", action="store_true")
    ra.add_argument("--yes", action="store_true")
    ra.add_argument("--verbose", "-v", action="store_true")
    ra.add_argument(
        "--all-keys",
        action="store_true",
        help="Include every non-empty key from files (ignores --prefix). "
        "PATCH only the listed keys; Render merges these into the service per API behavior — verify in staging.",
    )
    ra.set_defaults(func=cmd_render_api)

    rl = sub.add_parser("render-list", help="List services via render CLI (JSON -> id, name)")
    rl.set_defaults(func=cmd_render_list)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
