#!/usr/bin/env python3
"""Repair docstrings inserted inside multi-line function parameter lists."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = [
    ROOT / "tests" / "integration",
    ROOT / "tests" / "e2e",
    ROOT / "tests" / "smoke",
    ROOT / "tests" / "privacy",
    ROOT / "tests" / "eval",
    ROOT / "tests" / "bugs",
    ROOT / "tests" / "helpers",
    ROOT / "tests" / "conftest.py",
]


def iter_files() -> list[Path]:
    files: list[Path] = []
    for p in SCOPE:
        if p.is_file():
            files.append(p)
        else:
            files.extend(sorted(p.rglob("*.py")))
    return files


def repair(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"\s*(?:async\s+)?def \w+\(\s*$", line.rstrip("\n")):
            j = i + 1
            doc_line: str | None = None
            if j < len(lines) and '"""' in lines[j] and lines[j].strip().startswith('"""'):
                doc_line = lines[j]
                j += 1
            param_lines: list[str] = []
            while j < len(lines) and not lines[j].strip().startswith(")"):
                if '"""' not in lines[j]:
                    param_lines.append(lines[j])
                j += 1
            if j >= len(lines):
                out.append(line)
                i += 1
                continue
            close_line = lines[j]
            out.append(line)
            out.extend(param_lines)
            out.append(close_line)
            if doc_line is not None:
                indent_match = re.match(r"^(\s*)", close_line)
                indent: str = indent_match.group(1) if indent_match else ""
                normalized = doc_line if doc_line.startswith(indent) else indent + doc_line.lstrip()
                out.append(normalized)
            i = j + 1
            continue
        out.append(line)
        i += 1
    return out


def main() -> int:
    changed = 0
    for path in iter_files():
        original = path.read_text(encoding="utf-8")
        fixed = "".join(repair(original.splitlines(keepends=True)))
        if fixed != original:
            path.write_text(fixed, encoding="utf-8")
            changed += 1
    print(f"Repaired {changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
