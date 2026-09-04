#!/usr/bin/env python3
r"""List Vecinita-attributable DO / Modal resources for cost reviews (EV-323 / #323).

Filters shared-team DigitalOcean inventory so metar/empiric spend is excluded from
the Vecinita envelope (ADR-004 amendment EV-323).

Usage:
  # Filter names only (no network):
  uv run python scripts/ops/cost_attribution.py --dry-names \
    vecinita-staging-db metar-iwxxm empiric-mlflow-server

  # Live inventory (requires DIGITALOCEAN_TOKEN; Modal optional):
  set -a && source .env && set +a
  uv run python scripts/ops/cost_attribution.py --do --modal

Never prints secret values.

[Corpus: ADR-004] [Corpus: hosting] #323
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_VECINITA_NAME = re.compile(r"vecinita", re.IGNORECASE)
_EXCLUDED_NAME = re.compile(
    r"(?:metar[\-_]?iwxxm|empiric|mlflow|coder\d)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AttributionArgs:
    """CLI options for cost attribution."""

    dry_names: list[str]
    do: bool
    modal: bool
    as_json: bool


def is_vecinita_resource_name(name: str) -> bool:
    """Return True when a cloud resource name is Vecinita-attributable.

    Requires ``vecinita`` in the name and excludes known sibling project patterns
    (metar-iwxxm, empiric/mlflow) even if they somehow matched.
    """
    stripped = name.strip()
    if not stripped:
        return False
    if _EXCLUDED_NAME.search(stripped):
        return False
    return _VECINITA_NAME.search(stripped) is not None


def classify_names(names: list[str]) -> dict[str, list[str]]:
    """Split names into included (Vecinita) vs excluded."""
    included: list[str] = []
    excluded: list[str] = []
    for name in names:
        if is_vecinita_resource_name(name):
            included.append(name)
        else:
            excluded.append(name)
    return {"vecinita": included, "excluded": excluded}


def _do_get(path: str, *, token: str) -> object:
    req = urllib.request.Request(
        f"https://api.digitalocean.com/v2{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def fetch_do_projects(*, token: str) -> dict[str, object]:
    """Fetch DO projects and resolve resource URNs to names (EV-323)."""
    projects_raw = _do_get("/projects", token=token)
    projects = projects_raw.get("projects", []) if isinstance(projects_raw, dict) else []
    apps_raw = _do_get("/apps?per_page=200", token=token)
    apps_list = apps_raw.get("apps", []) if isinstance(apps_raw, dict) else []
    app_names: dict[str, str] = {}
    if isinstance(apps_list, list):
        for app in apps_list:
            if not isinstance(app, dict):
                continue
            raw_spec = app.get("spec")
            spec = raw_spec if isinstance(raw_spec, dict) else {}
            aid = str(app.get("id") or "")
            app_names[aid] = str(spec.get("name") or aid)

    dbs_raw = _do_get("/databases?per_page=200", token=token)
    dbs_list = dbs_raw.get("databases", []) if isinstance(dbs_raw, dict) else []
    db_names: dict[str, str] = {}
    if isinstance(dbs_list, list):
        for db in dbs_list:
            if isinstance(db, dict):
                db_names[str(db.get("id") or "")] = str(db.get("name") or "")

    drop_names: dict[str, str] = {}
    try:
        drops_raw = _do_get("/droplets?per_page=200", token=token)
        drops_list = drops_raw.get("droplets", []) if isinstance(drops_raw, dict) else []
        if isinstance(drops_list, list):
            for drop in drops_list:
                if isinstance(drop, dict):
                    drop_names[str(drop.get("id") or "")] = str(drop.get("name") or "")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError):
        pass

    out: dict[str, object] = {"projects": []}
    proj_rows: list[dict[str, object]] = []
    if isinstance(projects, list):
        for proj in projects:
            if not isinstance(proj, dict):
                continue
            pid = str(proj.get("id") or "")
            name = str(proj.get("name") or "")
            try:
                res_raw = _do_get(f"/projects/{pid}/resources", token=token)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError) as exc:
                proj_rows.append(
                    {
                        "id": pid,
                        "name": name,
                        "error": type(exc).__name__,
                        "resources": [],
                    }
                )
                continue
            resources = res_raw.get("resources", []) if isinstance(res_raw, dict) else []
            resolved: list[dict[str, str]] = []
            if isinstance(resources, list):
                for res in resources:
                    if not isinstance(res, dict):
                        continue
                    urn = str(res.get("urn") or "")
                    parts = urn.split(":")
                    kind = parts[1] if len(parts) > 1 else ""
                    rid = parts[2] if len(parts) > 2 else ""
                    rname = {
                        "app": app_names,
                        "dbaas": db_names,
                        "droplet": drop_names,
                    }.get(kind, {}).get(rid, "")
                    resolved.append(
                        {
                            "urn": urn,
                            "kind": kind,
                            "id": rid,
                            "name": rname,
                            "vecinita": "yes" if is_vecinita_resource_name(rname or "") else "no",
                        }
                    )
            proj_rows.append(
                {
                    "id": pid,
                    "name": name,
                    "environment": str(proj.get("environment") or ""),
                    "is_default": str(bool(proj.get("is_default"))).lower(),
                    "resources": resolved,
                }
            )
    out["projects"] = proj_rows
    return out


def fetch_do_inventory(*, token: str) -> dict[str, list[dict[str, str]]]:
    """Fetch DO apps / droplets / databases and split by Vecinita attribution."""
    out: dict[str, list[dict[str, str]]] = {
        "apps_vecinita": [],
        "apps_other": [],
        "droplets_vecinita": [],
        "droplets_other": [],
        "databases_vecinita": [],
        "databases_other": [],
        "errors": [],
    }

    def _bucket(kind: str, name: str, extra: dict[str, str]) -> None:
        row = {"name": name, **extra}
        key = f"{kind}_vecinita" if is_vecinita_resource_name(name) else f"{kind}_other"
        out[key].append(row)

    try:
        apps_raw = _do_get("/apps?per_page=200", token=token)
        apps = apps_raw.get("apps", []) if isinstance(apps_raw, dict) else []
        for app in apps if isinstance(apps, list) else []:
            if not isinstance(app, dict):
                continue
            raw_spec = app.get("spec")
            spec = raw_spec if isinstance(raw_spec, dict) else {}
            name = str(spec.get("name") or app.get("id") or "")
            _bucket("apps", name, {"id": str(app.get("id") or "")})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError) as exc:
        out["errors"].append({"where": "apps", "error": type(exc).__name__})

    try:
        drops_raw = _do_get("/droplets?per_page=200", token=token)
        drops = drops_raw.get("droplets", []) if isinstance(drops_raw, dict) else []
        for drop in drops if isinstance(drops, list) else []:
            if not isinstance(drop, dict):
                continue
            name = str(drop.get("name") or "")
            size = drop.get("size_slug")
            raw_size = drop.get("size")
            if size is None and isinstance(raw_size, dict):
                size = raw_size.get("slug")
            _bucket(
                "droplets",
                name,
                {"id": str(drop.get("id") or ""), "size": str(size or "")},
            )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError) as exc:
        out["errors"].append({"where": "droplets", "error": type(exc).__name__})

    try:
        dbs_raw = _do_get("/databases?per_page=200", token=token)
        dbs = dbs_raw.get("databases", []) if isinstance(dbs_raw, dict) else []
        for db in dbs if isinstance(dbs, list) else []:
            if not isinstance(db, dict):
                continue
            name = str(db.get("name") or "")
            _bucket(
                "databases",
                name,
                {
                    "engine": str(db.get("engine") or ""),
                    "size": str(db.get("size") or ""),
                },
            )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError) as exc:
        out["errors"].append({"where": "databases", "error": type(exc).__name__})

    return out


def fetch_modal_app_names() -> list[str]:
    """Return Modal app description lines via CLI (best-effort)."""
    try:
        proc = subprocess.run(
            ["modal", "app", "list", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    names: list[str] = []
    if isinstance(data, list):
        rows: object = data
    elif isinstance(data, dict):
        rows = data.get("apps")
    else:
        rows = []
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("Description") or row.get("description") or row.get("name") or "")
        if name:
            names.append(name)
    return names


def _parse_args(argv: list[str] | None = None) -> AttributionArgs:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--dry-names",
        nargs="*",
        default=[],
        help="Classify these names without calling APIs",
    )
    _ = parser.add_argument("--do", action="store_true", help="Fetch DO inventory")
    _ = parser.add_argument("--modal", action="store_true", help="List Modal apps via CLI")
    _ = parser.add_argument("--json", dest="as_json", action="store_true")
    ns = parser.parse_args(argv)
    return AttributionArgs(
        dry_names=list(ns.dry_names),
        do=bool(ns.do),
        modal=bool(ns.modal),
        as_json=bool(ns.as_json),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry."""
    args = _parse_args(argv)
    report: dict[str, object] = {}

    if args.dry_names:
        report["dry_names"] = classify_names(args.dry_names)

    if args.do:
        token = os.environ.get("DIGITALOCEAN_TOKEN", "").strip()
        if not token:
            print("DIGITALOCEAN_TOKEN unset", file=sys.stderr)
            return 2
        report["digitalocean"] = fetch_do_inventory(token=token)
        report["digitalocean_projects"] = fetch_do_projects(token=token)

    if args.modal:
        names = fetch_modal_app_names()
        report["modal"] = classify_names(names)

    if not report:
        print("Nothing to do: pass --dry-names, --do, and/or --modal", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
