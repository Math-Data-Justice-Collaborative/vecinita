#!/usr/bin/env python3
"""Validate committed required-check manifest and CI attestation (FR-005–FR-009)."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_MANIFEST_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _fail(category: str, scope: str, detail: str) -> None:
    """Emit FR-009 primary category (exact token) on stderr for automation."""
    _eprint(f"{category} [{scope}] {detail}")
    sys.exit(1)


def _read_json_file(path: Path, scope: str) -> Any:
    if not path.exists() or not path.is_file():
        _fail("missing_file", scope, f"not a readable file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _fail("io_or_parse", scope, f"read failed: {path}: {exc}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail("io_or_parse", scope, f"not valid UTF-8: {path}: {exc}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        _fail("io_or_parse", scope, f"invalid JSON: {path}: {exc}")


def _validate_manifest(data: Any, scope: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        _fail("schema", scope, "top-level value must be a JSON object")
    if "manifest_version" not in data:
        _fail("schema", scope, "missing manifest_version")
    if not isinstance(data.get("manifest_version"), int):
        _fail("schema", scope, "manifest_version must be an integer")
    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) == 0:
        _fail("schema", scope, "checks must be a non-empty array")
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for i, item in enumerate(checks):
        if not isinstance(item, dict):
            _fail("schema", scope, f"checks[{i}] must be an object")
        for k in item:
            if k not in ("id", "title", "description", "command"):
                _fail("schema", scope, f"checks[{i}] unknown property {k!r}")
        cid = item.get("id")
        title = item.get("title")
        command = item.get("command")
        if not isinstance(cid, str) or not _MANIFEST_ID_RE.match(cid):
            _fail("schema", scope, f"checks[{i}].id invalid or missing slug pattern")
        if not isinstance(title, str) or not title.strip():
            _fail("schema", scope, f"checks[{i}].title must be a non-empty string")
        if "description" in item and item["description"] is not None and not isinstance(item["description"], str):
            _fail("schema", scope, f"checks[{i}].description must be a string when present")
        if not isinstance(command, str) or not command.strip():
            _fail("schema", scope, f"checks[{i}].command must be a non-empty string")
        if cid in seen:
            _fail("schema", scope, f"duplicate manifest id {cid!r}")
        seen.add(cid)
        out.append(item)
    return out


def _parse_iso8601_utc(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def _validate_uuid_v4(run_id: str) -> None:
    try:
        u = uuid.UUID(run_id)
    except ValueError:
        _fail("schema", "attestation", "run_id is not a valid UUID")
    if u.version != 4:
        _fail("schema", "attestation", "run_id must be UUID version 4")


def _validate_attestation_v1(data: Any, scope: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        _fail("schema", scope, "top-level value must be a JSON object")
    allowed_top = {"format_version", "run_id", "generated_at", "git_head", "checks"}
    extra = set(data.keys()) - allowed_top
    if extra:
        _fail("schema", scope, f"unknown top-level properties: {sorted(extra)}")
    if data.get("format_version") != 1:
        _fail("schema", scope, "format_version must be 1 for v1 attestation")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or len(run_id) < 8:
        _fail("schema", scope, "run_id must be a string with minLength 8")
    _validate_uuid_v4(run_id)
    gen = data.get("generated_at")
    if not isinstance(gen, str):
        _fail("schema", scope, "generated_at must be a string")
    try:
        _parse_iso8601_utc(gen)
    except ValueError:
        _fail("schema", scope, "generated_at must be ISO-8601 parseable")
    if "git_head" in data:
        gh = data["git_head"]
        if not isinstance(gh, str) or not (7 <= len(gh) <= 40):
            _fail("schema", scope, "git_head must be a string of length 7–40 when present")
    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) < 1:
        _fail("schema", scope, "checks must be a non-empty array")
    for i, item in enumerate(checks):
        if not isinstance(item, dict):
            _fail("schema", scope, f"checks[{i}] must be an object")
        for k in item:
            if k not in ("id", "status", "finished_at"):
                _fail("schema", scope, f"checks[{i}] unknown property {k!r}")
        cid = item.get("id")
        st = item.get("status")
        if not isinstance(cid, str) or not _MANIFEST_ID_RE.match(cid):
            _fail("schema", scope, f"checks[{i}].id invalid")
        if st not in ("passed", "failed"):
            _fail("schema", scope, f"checks[{i}].status must be passed or failed")
        if "finished_at" in item and item["finished_at"] is not None:
            ft = item["finished_at"]
            if not isinstance(ft, str):
                _fail("schema", scope, f"checks[{i}].finished_at must be a string")
            try:
                _parse_iso8601_utc(ft)
            except ValueError:
                _fail("schema", scope, f"checks[{i}].finished_at invalid ISO-8601")
    return data


def _validate_attestation_v2(data: Any, scope: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        _fail("schema", scope, "top-level value must be a JSON object")
    allowed_top = {"format_version", "run_id", "generated_at", "git_head", "checks"}
    extra = set(data.keys()) - allowed_top
    if extra:
        _fail("schema", scope, f"unknown top-level properties: {sorted(extra)}")
    if data.get("format_version") != 2:
        _fail("schema", scope, "format_version must be 2 for v2 attestation")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or len(run_id) < 8:
        _fail("schema", scope, "run_id must be a string with minLength 8")
    _validate_uuid_v4(run_id)
    gen = data.get("generated_at")
    if not isinstance(gen, str):
        _fail("schema", scope, "generated_at must be a string")
    try:
        _parse_iso8601_utc(gen)
    except ValueError:
        _fail("schema", scope, "generated_at must be ISO-8601 parseable")
    gh = data.get("git_head")
    if not isinstance(gh, str) or not (7 <= len(gh) <= 40):
        _fail("schema", scope, "git_head must be a string of length 7–40")
    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) < 1:
        _fail("schema", scope, "checks must be a non-empty array")
    for i, item in enumerate(checks):
        if not isinstance(item, dict):
            _fail("schema", scope, f"checks[{i}] must be an object")
        for k in item:
            if k not in (
                "id",
                "title",
                "command",
                "status",
                "exit_code",
                "started_at",
                "finished_at",
                "duration_seconds",
                "stdout",
                "stderr",
            ):
                _fail("schema", scope, f"checks[{i}] unknown property {k!r}")
        cid = item.get("id")
        title = item.get("title")
        command = item.get("command")
        st = item.get("status")
        exit_code = item.get("exit_code")
        started_at = item.get("started_at")
        finished_at = item.get("finished_at")
        duration_seconds = item.get("duration_seconds")
        stdout_text = item.get("stdout")
        stderr_text = item.get("stderr")
        if not isinstance(cid, str) or not _MANIFEST_ID_RE.match(cid):
            _fail("schema", scope, f"checks[{i}].id invalid")
        if not isinstance(title, str) or not title.strip():
            _fail("schema", scope, f"checks[{i}].title must be a non-empty string")
        if not isinstance(command, str) or not command.strip():
            _fail("schema", scope, f"checks[{i}].command must be a non-empty string")
        if st not in ("passed", "failed"):
            _fail("schema", scope, f"checks[{i}].status must be passed or failed")
        if not isinstance(exit_code, int):
            _fail("schema", scope, f"checks[{i}].exit_code must be an integer")
        if not isinstance(started_at, str):
            _fail("schema", scope, f"checks[{i}].started_at must be a string")
        if not isinstance(finished_at, str):
            _fail("schema", scope, f"checks[{i}].finished_at must be a string")
        if not isinstance(duration_seconds, int | float) or duration_seconds < 0:
            _fail("schema", scope, f"checks[{i}].duration_seconds must be non-negative number")
        if not isinstance(stdout_text, str):
            _fail("schema", scope, f"checks[{i}].stdout must be a string")
        if not isinstance(stderr_text, str):
            _fail("schema", scope, f"checks[{i}].stderr must be a string")
        try:
            _parse_iso8601_utc(started_at)
            _parse_iso8601_utc(finished_at)
        except ValueError:
            _fail("schema", scope, f"checks[{i}] started_at/finished_at must be ISO-8601")
    return data


def _validate_attestation(data: Any, scope: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        _fail("schema", scope, "top-level value must be a JSON object")
    version = data.get("format_version")
    if version == 1:
        return _validate_attestation_v1(data, scope)
    if version == 2:
        return _validate_attestation_v2(data, scope)
    _fail("schema", scope, f"unsupported format_version {version!r}")


def _staleness_fail(generated_at: datetime, start: datetime, max_age: timedelta) -> bool:
    return (start - generated_at) > max_age


def _validate_coverage(manifest_ids: list[str], attestation: dict[str, Any], scope: str) -> None:
    checks = attestation.get("checks")
    assert isinstance(checks, list)
    by_id: dict[str, list[str]] = {}
    for item in checks:
        assert isinstance(item, dict)
        cid = item["id"]
        st = item["status"]
        by_id.setdefault(cid, []).append(st)
    for mid in manifest_ids:
        if mid not in by_id:
            _fail("incomplete_manifest", scope, f"missing check id {mid!r} in attestation")
        if len(by_id[mid]) != 1:
            _fail("incomplete_manifest", scope, f"duplicate check id {mid!r} in attestation")
        if by_id[mid][0] != "passed":
            _fail("failed_check", scope, f"check {mid!r} is not passed")
    for cid in by_id:
        if cid not in set(manifest_ids):
            _fail("incomplete_manifest", scope, f"unexpected attestation id {cid!r} not in manifest")


def _resolve_local_head(short_len: int) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", f"--short={short_len}", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        _fail("io_or_parse", "validator", f"failed to resolve current HEAD: {exc}")
    if proc.returncode != 0:
        _fail("io_or_parse", "validator", f"failed to resolve current HEAD: {proc.stderr.strip()}")
    resolved = proc.stdout.strip()
    if not resolved:
        _fail("io_or_parse", "validator", "failed to resolve current HEAD")
    return resolved


def _normalize_expected_head(expected_head: str, short_len: int) -> str:
    normalized = expected_head.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", normalized):
        _fail("schema", "validator", "expected_git_head must be a hex SHA (7-40 chars)")
    return normalized.lower()[:short_len]


def _is_ancestor(commit: str, descendant: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, descendant],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        _fail("io_or_parse", "validator", f"failed ancestry check: {exc}")
    if proc.returncode == 0:
        return True
    if proc.returncode in (1, 128):
        return False
    _fail("io_or_parse", "validator", f"failed ancestry check: {proc.stderr.strip()}")
    return False


def _validate_git_head(attestation: dict[str, Any], expected_git_head: str | None = None) -> None:
    git_head = attestation.get("git_head")
    if not isinstance(git_head, str) or not git_head.strip():
        _fail("schema", "attestation", "git_head is required for commit-based validation")
    expected = expected_git_head.strip() if isinstance(expected_git_head, str) else ""
    if expected:
        resolved = _normalize_expected_head(expected, len(git_head))
    else:
        resolved = _resolve_local_head(len(git_head))
    # The attestation is generated before it is committed, so allow it to be
    # either the exact expected commit or an ancestor of it.
    if resolved != git_head and not _is_ancestor(git_head, resolved):
        _fail(
            "staleness",
            "attestation",
            f"git_head {git_head!r} is not equal to or ancestor of current HEAD {resolved!r}",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(".ci/required-checks.json"),
        help="Path to required-check manifest JSON",
    )
    parser.add_argument(
        "--attestation",
        type=Path,
        default=Path(".ci/ci-attestation.json"),
        help="Path to CI attestation JSON",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=48.0,
        help="Maximum attestation age in hours (FR-006)",
    )
    parser.add_argument(
        "--expected-git-head",
        type=str,
        default="",
        help="Expected commit SHA for attestation git_head (e.g., PR head SHA)",
    )
    args = parser.parse_args()

    env_hours = os.environ.get("CI_ATTESTATION_MAX_AGE_HOURS")
    if env_hours is not None and env_hours.strip() != "":
        try:
            args.max_age_hours = float(env_hours)
        except ValueError:
            _fail("io_or_parse", "validator", f"invalid CI_ATTESTATION_MAX_AGE_HOURS={env_hours!r}")

    manifest_path = args.manifest.resolve()
    attestation_path = args.attestation.resolve()

    m_data = _read_json_file(manifest_path, "manifest")
    manifest_checks = _validate_manifest(m_data, "manifest")
    manifest_ids = [c["id"] for c in manifest_checks]

    a_data = _read_json_file(attestation_path, "attestation")
    attestation = _validate_attestation(a_data, "attestation")

    gen_raw = attestation["generated_at"]
    assert isinstance(gen_raw, str)
    generated_at = _parse_iso8601_utc(gen_raw)
    start = datetime.now(timezone.utc)
    max_age = timedelta(hours=args.max_age_hours)
    if _staleness_fail(generated_at, start, max_age):
        _fail("staleness", "attestation", "generated_at is outside the configured freshness window")

    _validate_git_head(attestation, args.expected_git_head)
    _validate_coverage(manifest_ids, attestation, "attestation")

    sys.exit(0)


if __name__ == "__main__":
    main()
