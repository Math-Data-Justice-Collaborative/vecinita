#!/usr/bin/env python3
"""Run manifest commands and write .ci/ci-attestation.json (FR-002)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
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


def _run_check(command: str, cwd: Path) -> int:
    """Run shell command with bash strict mode semantics."""
    script = f"set -euo pipefail; {command}"
    proc = subprocess.run(
        ["bash", "-lc", script],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return proc.returncode


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
        cmd = entry["command"]
        code = _run_check(cmd, repo)
        ok = code == 0
        if not ok:
            any_failed = True
        item: dict[str, Any] = {
            "id": cid,
            "status": "passed" if ok else "failed",
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
        "format_version": 1,
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
