#!/usr/bin/env python3
"""Insert explicit '+' between adjacent implicit string-literal lines."""

from __future__ import annotations

import sys
from pathlib import Path

ROOTS = ("apps", "packages", "tests", "infra", "scripts")


def fix_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    idx = 0
    while idx < len(lines) - 1:
        cur = lines[idx].rstrip()
        nxt = lines[idx + 1].lstrip()
        if nxt.startswith(('"""', "'''")):
            idx += 1
            continue
        next_is_string = nxt.startswith(('"', "'", 'f"', "f'", 'F"', "F'"))
        if (
            (cur.endswith(('"', "'")))
            and not cur.endswith("+")
            and next_is_string
            and not cur.strip().startswith("#")
        ):
            lines[idx] = cur + " +\n"
            changed = True
        idx += 1
    if changed:
        _ = path.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    repo = Path.cwd()
    changed_files = 0
    for root in ROOTS:
        for path in (repo / root).rglob("*.py"):
            if fix_file(path):
                changed_files += 1
    print(f"fixed {changed_files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
