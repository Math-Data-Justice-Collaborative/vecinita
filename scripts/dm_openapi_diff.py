#!/usr/bin/env python3
"""Fetch the DM (scraper) OpenAPI document and diff it against a committed snapshot (FR-004 / SC-002).

Usage:
  python scripts/dm_openapi_diff.py              # diff live URL vs snapshot
  python scripts/dm_openapi_diff.py --write     # refresh snapshot from live URL

Env:
  DATA_MANAGEMENT_SCHEMA_URL — OpenAPI URL (default: same as backend integration test).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

DEFAULT_URL = "https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def snapshot_path() -> Path:
    return (
        repo_root()
        / "specs"
        / "005-wire-services-dm-front"
        / "artifacts"
        / "dm-openapi.snapshot.json"
    )


def normalize(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def fetch_openapi(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    env_url = (os.environ.get("DATA_MANAGEMENT_SCHEMA_URL") or "").strip()
    parser.add_argument(
        "--url",
        default=env_url or DEFAULT_URL,
        help="OpenAPI JSON URL",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write fetched document to the snapshot path instead of diffing",
    )
    args = parser.parse_args()

    path = snapshot_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        live = fetch_openapi(args.url)
    except OSError as exc:
        print(f"dm_openapi_diff: failed to fetch {args.url}: {exc}", file=sys.stderr)
        return 2

    if args.write:
        path.write_text(normalize(live), encoding="utf-8")
        print(f"Wrote snapshot to {path}")
        return 0

    if not path.is_file():
        print(
            f"dm_openapi_diff: missing snapshot {path}; run with --write first",
            file=sys.stderr,
        )
        return 2

    expected = json.loads(path.read_text(encoding="utf-8"))
    if normalize(live) != normalize(expected):
        print("dm_openapi_diff: OpenAPI document differs from snapshot.", file=sys.stderr)
        print(f"  snapshot: {path}", file=sys.stderr)
        print(f"  source:   {args.url}", file=sys.stderr)
        return 1

    print("dm_openapi_diff: snapshot matches fetched OpenAPI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
