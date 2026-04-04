#!/usr/bin/env python3
"""Validate Render service runtime mode via Render API.

Usage:
  python scripts/github/validate_render_runtime.py \
    --service-id srv-abc123 --service-name vecinita-gateway --expect docker

Environment:
  RENDER_API_KEY  Render API key with access to target service(s)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


RENDER_API_BASE = "https://api.render.com/v1"


def _http_get_json(url: str, api_key: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _service_payload(raw: dict) -> dict:
    if isinstance(raw, dict) and isinstance(raw.get("service"), dict):
        return raw["service"]
    return raw


def _runtime_candidates(service: dict) -> list[tuple[str, str]]:
    details = service.get("serviceDetails") if isinstance(service, dict) else {}
    if not isinstance(details, dict):
        details = {}

    def _norm(value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    candidates = [
        ("runtime", _norm(service.get("runtime"))),
        ("env", _norm(service.get("env"))),
        ("serviceDetails.runtime", _norm(details.get("runtime"))),
        ("serviceDetails.env", _norm(details.get("env"))),
    ]
    return [(path, value) for path, value in candidates if value]


def _is_expected_runtime(candidates: list[tuple[str, str]], expected: str) -> tuple[bool | None, str]:
    expected = expected.strip().lower()
    if not candidates:
        return None, "No runtime fields were present in the Render service payload"

    for path, value in candidates:
        if value == expected:
            return True, f"Matched {path}={value}"

    observed = ", ".join(f"{path}={value}" for path, value in candidates)
    return False, f"Observed runtime fields: {observed}"


def validate_service(service_id: str, service_name: str, expected_runtime: str, api_key: str) -> int:
    label = service_name or service_id
    url = f"{RENDER_API_BASE}/services/{service_id}"
    try:
        raw = _http_get_json(url, api_key)
    except urllib.error.HTTPError as exc:
        print(f"[render-runtime-check] {label}: HTTP {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[render-runtime-check] {label}: request failed: {exc}", file=sys.stderr)
        return 1

    service = _service_payload(raw)
    candidates = _runtime_candidates(service)
    ok, detail = _is_expected_runtime(candidates, expected_runtime)
    if ok is True:
        print(f"[render-runtime-check] PASS {label}: expected={expected_runtime}; {detail}")
        return 0
    if ok is None:
        print(
            f"[render-runtime-check] FAIL {label}: expected={expected_runtime}; {detail}",
            file=sys.stderr,
        )
        return 1

    print(f"[render-runtime-check] FAIL {label}: expected={expected_runtime}; {detail}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Render runtime mode for one or more services")
    parser.add_argument("--service-id", required=True, help="Render service ID (srv-...)")
    parser.add_argument(
        "--service-name",
        default="",
        help="Human-friendly service name for logs",
    )
    parser.add_argument(
        "--expect",
        default="docker",
        help="Expected runtime value (default: docker)",
    )
    args = parser.parse_args()

    api_key = os.getenv("RENDER_API_KEY", "").strip()
    if not api_key:
        print("RENDER_API_KEY environment variable is required", file=sys.stderr)
        return 1

    return validate_service(args.service_id, args.service_name, args.expect, api_key)


if __name__ == "__main__":
    raise SystemExit(main())
