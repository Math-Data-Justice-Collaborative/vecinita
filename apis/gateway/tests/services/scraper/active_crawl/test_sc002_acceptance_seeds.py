"""Validate ACCEPTANCE_SEEDS.md host list (SC-002 file slice)."""

from __future__ import annotations

import re
from pathlib import Path

_SEEDS = Path(__file__).resolve().parent / "ACCEPTANCE_SEEDS.md"


def test_acceptance_seeds_file_nonempty_hosts() -> None:
    text = _SEEDS.read_text(encoding="utf-8")
    hosts: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        assert " " not in s, f"unexpected whitespace in host line: {line!r}"
        assert re.match(r"^[a-z0-9.-]+$", s), f"host line looks invalid: {line!r}"
        hosts.append(s)
    assert len(hosts) >= 5
    assert len(hosts) == len(set(hosts))
