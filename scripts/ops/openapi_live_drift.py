"""Compare checked-in OpenAPI YAML against live `/openapi.json` (TC-337).

Prefer live OpenAPI for Schemathesis; use this drift check weekly (or after
OpenAPI-affecting deploys) so repo SoT and staging stay aligned.

[Corpus: api] [Corpus: staging] [Spec: docs/test-plan.md §TC-337]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_REPO_ROOT = Path(__file__).resolve().parents[2]
_OPENAPI_DIR = _REPO_ROOT / "openapi"

_SURFACE_FILES: dict[str, str] = {
    "chat-rag": "chat-rag.yaml",
    "internal-write": "internal-write.yaml",
    "data-management": "data-management.yaml",
}

_REQUIRED_SCHEMES: dict[str, frozenset[str]] = {
    "internal-write": frozenset({"bearerAuth", "internalApiKey"}),
    "data-management": frozenset({"bearerAuth", "modalProxyAuth"}),
}


def normalize_path(path: str, servers_url: str) -> str:
    """Join relative OpenAPI path with servers.url; leave absolute paths alone.

    Repo YAML often uses template bases like ``https://{host}/api/v1``; only the
    URL path prefix is applied so keys match live FastAPI ``/api/v1/...`` paths.
    """
    path_part = path if path.startswith("/") else f"/{path}"
    base_raw = servers_url.strip()
    if not base_raw:
        return path_part
    if "://" in base_raw or base_raw.startswith("//"):
        parsed = urlsplit(base_raw if "://" in base_raw else f"https:{base_raw}")
        base = parsed.path or "/"
    else:
        base = base_raw if base_raw.startswith("/") else f"/{base_raw}"
    base = base.rstrip("/") or ""
    if not base:
        return path_part
    if path_part == base or path_part.startswith(f"{base}/"):
        return path_part
    return f"{base}{path_part}"


def _servers_url(spec: JsonObject) -> str:
    servers = spec.get("servers")
    if not isinstance(servers, list) or not servers:
        return ""
    first = servers[0]
    if not isinstance(first, dict):
        return ""
    url = first.get("url")
    return str(url) if isinstance(url, str) else ""


def _paths_object(spec: JsonObject) -> JsonObject:
    paths = spec.get("paths")
    return as_json_object(paths) if isinstance(paths, dict) else {}


def _security_scheme_names(spec: JsonObject) -> set[str]:
    components = spec.get("components")
    if not isinstance(components, dict):
        return set()
    schemes = components.get("securitySchemes")
    if not isinstance(schemes, dict):
        return set()
    return {str(name) for name in schemes}


def required_security_scheme_names(surface: str) -> set[str]:
    """Scheme names expected on live OpenAPI for a surface (TC-335)."""
    return set(_REQUIRED_SCHEMES.get(surface, frozenset()))


def drift_messages(repo: JsonObject, live: JsonObject, *, surface: str) -> list[str]:
    """Return human-readable drift lines (empty when aligned)."""
    msgs: list[str] = []
    prefix = _servers_url(repo)
    repo_paths = _paths_object(repo)
    live_paths = _paths_object(live)

    for raw_path, path_item_obj in repo_paths.items():
        if not isinstance(path_item_obj, dict):
            continue
        path_item = cast("JsonObject", path_item_obj)
        abs_path = normalize_path(str(raw_path), prefix)
        live_item_obj = live_paths.get(abs_path)
        if not isinstance(live_item_obj, dict):
            continue
        live_item = cast("JsonObject", live_item_obj)
        for method, op_obj in path_item.items():
            method_l = str(method).lower()
            if method_l not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(op_obj, dict):
                continue
            repo_op = cast("JsonObject", op_obj)
            live_op_obj = live_item.get(method_l)
            if not isinstance(live_op_obj, dict):
                msgs.append(
                    f"{surface} {method_l.upper()} {abs_path}: present in repo, missing on live",
                )
                continue
            live_op = cast("JsonObject", live_op_obj)
            if "requestBody" in repo_op and "requestBody" not in live_op:
                detail = (
                    f"{surface} {method_l.upper()} {abs_path}: "
                    + "repo has requestBody but live OpenAPI does not"
                )
                msgs.append(detail)

    required = required_security_scheme_names(surface)
    if required:
        live_schemes = _security_scheme_names(live)
        missing = sorted(required - live_schemes)
        if missing:
            msgs.append(f"{surface} securitySchemes missing: {', '.join(missing)}")

    return msgs


def load_repo_spec(surface: str) -> JsonObject:
    """Load checked-in OpenAPI YAML for a named surface."""
    filename = _SURFACE_FILES.get(surface)
    if filename is None:
        msg = f"unknown surface {surface!r}; choose from {sorted(_SURFACE_FILES)}"
        raise ValueError(msg)
    raw = yaml.safe_load((_OPENAPI_DIR / filename).read_text(encoding="utf-8"))
    return as_json_object(raw)


def fetch_live_openapi(url: str, *, timeout_s: float = 30.0) -> JsonObject:
    """GET live OpenAPI JSON (prefer ``…/openapi.json``)."""
    req = Request(url, headers={"Accept": "application/json"})  # noqa: S310
    with urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    return as_json_object(payload)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI for weekly / post-deploy OpenAPI drift checks."""
    parser = argparse.ArgumentParser(
        description="Compare repo openapi/*.yaml to live /openapi.json (TC-337).",
    )
    _ = parser.add_argument(
        "--surface",
        choices=sorted(_SURFACE_FILES),
        required=True,
        help="Which checked-in OpenAPI file to compare",
    )
    _ = parser.add_argument(
        "--live-url",
        required=True,
        help="Full URL to live OpenAPI JSON (e.g. $VECINITA_STAGING_CHAT_URL/openapi.json)",
    )
    _ = parser.add_argument(
        "--timeout-s",
        type=float,
        default=30.0,
        help="HTTP timeout seconds (default 30)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Exit 0 when aligned; 1 on drift; 2 on fetch/parse errors."""
    args = parse_args(argv)
    try:
        repo = load_repo_spec(str(args.surface))
        live = fetch_live_openapi(str(args.live_url), timeout_s=float(args.timeout_s))
    except (OSError, ValueError, HTTPError, URLError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    msgs = drift_messages(repo, live, surface=str(args.surface))
    if not msgs:
        print(f"OK: {args.surface} aligned with {args.live_url}")
        return 0
    print(f"DRIFT: {args.surface} vs {args.live_url}", file=sys.stderr)
    for line in msgs:
        print(f"  - {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
