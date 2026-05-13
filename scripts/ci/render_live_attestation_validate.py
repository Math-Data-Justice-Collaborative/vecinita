#!/usr/bin/env python3
"""Validate committed Render preview live attestation for PR merge gating."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_TITLE_TOKEN = "[render preview]"
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def _parse_iso8601_utc(value: str) -> datetime:
    raw = value
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        _fail(f"missing render live attestation file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"invalid render live attestation JSON: {exc}")
    if not isinstance(data, dict):
        _fail("render live attestation must be a JSON object")
    return data


def _normalize_expected_head(expected: str, short_len: int) -> str:
    value = expected.strip().lower()
    if not _SHA_RE.fullmatch(value):
        _fail("--expected-git-head must be 7-40 lowercase/uppercase hex chars")
    return value[:short_len]


def _is_ancestor(commit: str, descendant: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, descendant],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--attestation",
        type=Path,
        default=Path(".ci/render-live-attestation.json"),
        help="Path to committed Render preview live attestation JSON.",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=24.0,
        help="Maximum allowed attestation age in hours.",
    )
    parser.add_argument(
        "--expected-git-head",
        type=str,
        default="",
        help="Expected PR head SHA; attestation git_head must match or be ancestor.",
    )
    parser.add_argument(
        "--expected-pr-title",
        type=str,
        default="",
        help="Optional PR title from event payload to verify token requirement.",
    )
    args = parser.parse_args()

    data = _read_json(args.attestation.resolve())
    if data.get("format_version") != 1:
        _fail("render live attestation format_version must be 1")

    generated_at = data.get("generated_at")
    if not isinstance(generated_at, str):
        _fail("render live attestation generated_at must be a string")
    try:
        generated_dt = _parse_iso8601_utc(generated_at)
    except ValueError as exc:
        _fail(f"render live attestation generated_at is invalid ISO-8601: {exc}")

    age = datetime.now(timezone.utc) - generated_dt
    if age > timedelta(hours=args.max_age_hours):
        _fail("render live attestation is stale; regenerate live checks")

    pr_title = data.get("pr_title")
    if not isinstance(pr_title, str) or _TITLE_TOKEN not in pr_title.lower():
        _fail("render live attestation pr_title must include [render preview]")

    if args.expected_pr_title and _TITLE_TOKEN not in args.expected_pr_title.lower():
        _fail("pull request title must include [render preview]")

    git_head = data.get("git_head")
    if not isinstance(git_head, str) or not _SHA_RE.fullmatch(git_head.lower()):
        _fail("render live attestation git_head must be a 7-40 char hex SHA")
    git_head = git_head.lower()

    if args.expected_git_head:
        expected = _normalize_expected_head(args.expected_git_head, len(git_head))
        if expected != git_head and not _is_ancestor(git_head, expected):
            _fail("render live attestation git_head must match or be ancestor of expected head")

    status = data.get("status")
    if status != "passed":
        _fail("render live attestation status must be passed")

    live_checks = data.get("live_checks")
    if not isinstance(live_checks, list) or not live_checks:
        _fail("render live attestation live_checks must be a non-empty array")
    for idx, check in enumerate(live_checks):
        if not isinstance(check, dict):
            _fail(f"live_checks[{idx}] must be an object")
        cid = check.get("id")
        cstatus = check.get("status")
        url = check.get("url")
        if not isinstance(cid, str) or not cid.strip():
            _fail(f"live_checks[{idx}].id must be a non-empty string")
        if cstatus != "passed":
            _fail(f"live_checks[{idx}] is not passed")
        if not isinstance(url, str) or not url.startswith("https://"):
            _fail(f"live_checks[{idx}].url must be an https URL")

    print("render live attestation valid")


if __name__ == "__main__":
    main()
