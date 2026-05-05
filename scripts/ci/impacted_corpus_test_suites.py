#!/usr/bin/env python3
"""Determine impacted test suites for feature 017 corpus-sync changes."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class SuiteRule:
    suite: str
    prefixes: tuple[str, ...]


SUITE_RULES: tuple[SuiteRule, ...] = (
    SuiteRule(
        "pact",
        (
            "frontends/chat/tests/pact/",
            "frontends/data-management/tests/pact/",
            "apis/gateway/tests/pact/",
            "backend/tests/pact/",
        ),
    ),
    SuiteRule(
        "contract",
        (
            "apis/gateway/tests/contracts/",
            "backend/tests/contracts/",
            "apis/data-management-api/tests/",
            "specs/017-canonical-postgres-sync/contracts/",
        ),
    ),
    SuiteRule(
        "integration",
        (
            "apis/gateway/tests/integration/",
            "backend/tests/integration/",
            "apis/gateway/src/",
            "backend/src/",
            "apis/data-management-api/apps/backend/",
        ),
    ),
    SuiteRule("system", ("frontends/chat/tests/e2e/", "frontends/chat/src/features/documents/", "frontends/data-management/src/")),
)

SUITE_COMMANDS: dict[str, str] = {
    "pact": "make pact-verify-providers",
    "contract": "cd apis/gateway && uv run pytest tests/contracts -m contract -q --tb=short",
    "integration": "make test-integration",
    "system": "cd frontends/chat && npm run test:e2e",
}


def _git_changed_files() -> list[str]:
    cmd = ["git", "diff", "--name-only", "HEAD"]
    output = subprocess.check_output(cmd, text=True).strip()
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def classify_suites(changed_files: list[str]) -> list[str]:
    impacted: set[str] = set()
    for path in changed_files:
        for rule in SUITE_RULES:
            if any(path.startswith(prefix) for prefix in rule.prefixes):
                impacted.add(rule.suite)
    return sorted(impacted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("impacted", "full"), default="impacted")
    parser.add_argument("--emit-json", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if args.mode == "full":
        suites = [rule.suite for rule in SUITE_RULES]
        changed = []
    else:
        changed = _git_changed_files()
        suites = classify_suites(changed)

    payload = {"mode": args.mode, "changed_files": changed, "suites": suites}
    if args.emit_json:
        print(json.dumps(payload, indent=2))
    else:
        print(" ".join(suites))

    if args.run:
        for suite in suites:
            command = SUITE_COMMANDS[suite]
            subprocess.check_call(command, shell=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
