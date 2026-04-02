#!/usr/bin/env python3
"""Poll Render API until a service deploy reaches 'live' status.

Usage:
    python wait_for_render_deploy.py <service_id> [--timeout 900] [--interval 30]

Environment:
    RENDER_API_KEY  -- Render API key with read access to the target service

Exit codes:
    0  -- deploy reached 'live' within the timeout
    1  -- timeout elapsed or deploy entered a failure state
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request
import json


RENDER_API_BASE = "https://api.render.com/v1"
TERMINAL_STATES = {"live", "failed", "canceled", "deactivated"}
SUCCESS_STATE = "live"


def _latest_deploy(service_id: str, api_key: str) -> dict | None:
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys?limit=1"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list) and data:
                return data[0].get("deploy", data[0])
            return None
    except urllib.error.HTTPError as exc:
        print(f"[wait_for_render_deploy] HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"[wait_for_render_deploy] Request error: {exc}", file=sys.stderr)
        return None


def wait_for_deploy(
    service_id: str,
    api_key: str,
    *,
    timeout_seconds: int = 900,
    poll_interval_seconds: int = 30,
) -> bool:
    """Poll until the newest deploy for *service_id* reaches a terminal state.

    Returns True if status == 'live', False otherwise.
    """
    deadline = time.monotonic() + timeout_seconds
    print(f"[wait_for_render_deploy] Watching service {service_id} (timeout={timeout_seconds}s)")

    while time.monotonic() < deadline:
        deploy = _latest_deploy(service_id, api_key)
        if deploy is None:
            print("[wait_for_render_deploy] Could not retrieve deploy info; retrying…")
        else:
            status = deploy.get("status", "unknown")
            deploy_id = deploy.get("id", "?")
            print(f"[wait_for_render_deploy] deploy={deploy_id} status={status}")
            if status in TERMINAL_STATES:
                if status == SUCCESS_STATE:
                    print(f"[wait_for_render_deploy] Deploy {deploy_id} is live ✓")
                    return True
                else:
                    print(
                        f"[wait_for_render_deploy] Deploy {deploy_id} ended with status={status}",
                        file=sys.stderr,
                    )
                    return False

        remaining = deadline - time.monotonic()
        sleep = min(poll_interval_seconds, max(0, remaining))
        if sleep > 0:
            time.sleep(sleep)

    print(
        f"[wait_for_render_deploy] Timeout after {timeout_seconds}s — deploy did not reach 'live'",
        file=sys.stderr,
    )
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Wait for a Render service deploy to go live.")
    parser.add_argument("service_id", help="Render service ID (e.g. srv-abc123)")
    parser.add_argument(
        "--timeout", type=int, default=900, help="Maximum seconds to wait (default: 900)"
    )
    parser.add_argument(
        "--interval", type=int, default=30, help="Poll interval in seconds (default: 30)"
    )
    args = parser.parse_args()

    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        print("RENDER_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    success = wait_for_deploy(
        args.service_id,
        api_key,
        timeout_seconds=args.timeout,
        poll_interval_seconds=args.interval,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
