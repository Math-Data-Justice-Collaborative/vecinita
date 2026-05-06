#!/usr/bin/env python3
"""Run manifest commands and write .ci/ci-attestation.json (FR-002)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from time import monotonic
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("checks"), list):
        sys.exit("manifest invalid: expected object with checks array")
    checks = data["checks"]
    out: list[dict[str, Any]] = []
    for item in checks:
        if isinstance(item, dict) and isinstance(item.get("command"), str) and isinstance(item.get("id"), str):
            out.append(item)
    return out


def _run_check_detailed(command: str, cwd: Path) -> tuple[int, str, str, str, str, float]:
    start_dt = datetime.now(timezone.utc)
    start_mono = monotonic()
    script = f"set -euo pipefail; {command}"
    proc = subprocess.run(
        ["bash", "-lc", script],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    elapsed = monotonic() - start_mono
    end_dt = datetime.now(timezone.utc)
    started_at = start_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    finished_at = end_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return (
        proc.returncode,
        proc.stdout,
        proc.stderr,
        started_at,
        finished_at,
        round(elapsed, 3),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path(".ci/required-checks.json"))
    parser.add_argument("--attestation", type=Path, default=Path(".ci/ci-attestation.json"))
    args = parser.parse_args()

    repo = _repo_root()
    manifest_path = (repo / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest
    attestation_path = (repo / args.attestation).resolve() if not args.attestation.is_absolute() else args.attestation

    checks_def = _load_manifest(manifest_path)
    results: list[dict[str, Any]] = []
    any_failed = False

    for entry in checks_def:
        cid = entry["id"]
        title = entry.get("title", cid)
        cmd = entry["command"]
        code, stdout_text, stderr_text, started_at, finished_at, duration_seconds = _run_check_detailed(cmd, repo)
        ok = code == 0
        if not ok:
            any_failed = True
        item: dict[str, Any] = {
            "id": cid,
            "title": title,
            "command": cmd,
            "status": "passed" if ok else "failed",
            "exit_code": code,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": duration_seconds,
            "stdout": stdout_text,
            "stderr": stderr_text,
        }
        results.append(item)

    run_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    git_head: str | None = None
    try:
        gh = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if gh.returncode == 0 and gh.stdout.strip():
            git_head = gh.stdout.strip()[:40]
    except OSError:
        pass

    payload: dict[str, Any] = {
        "format_version": 2,
        "run_id": run_id,
        "generated_at": generated_at,
        "checks": results,
    }
    if git_head:
        payload["git_head"] = git_head

    attestation_path.parent.mkdir(parents=True, exist_ok=True)
    attestation_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if any_failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
