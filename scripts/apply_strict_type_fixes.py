#!/usr/bin/env python3
"""Surgical basedpyright strict-delta fixes from --outputjson (no ast.unparse)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_SKIP_FILES = frozenset({"scripts/apply_strict_type_fixes.py"})
_PYRIGHT_IGNORE = re.compile(r"\s*#\s*pyright:\s*ignore\[[^\]]+\](?:\s*#.*)?$")
_TYPE_IGNORE = re.compile(r"\s*#\s*type:\s*ignore(?:\[[^\]]+\])?(?:\s*#.*)?$")
_BLOCKED_PREFIXES = (
    "return ",
    "raise ",
    "yield ",
    "assert ",
    "_ = ",
    "del ",
    "pass",
    "break",
    "continue",
    "if ",
    "elif ",
    "else:",
    "while ",
    "for ",
    "with ",
    "def ",
    "class ",
    "async def ",
    "@",
)


def _repo_relative(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _statement_start_line(lines: list[str], line_idx: int) -> int:
    idx = line_idx
    while idx > 0:
        prev = lines[idx - 1].rstrip()
        if not prev:
            break
        if prev.endswith((",", "(", "[", "{", "\\")):
            idx -= 1
            continue
        if not prev.strip().startswith("#"):
            break
        idx -= 1
    return idx


def _fix_unused_call_result(lines: list[str], line_idx: int) -> bool:
    start = _statement_start_line(lines, line_idx)
    line = lines[start]
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#"):
        return False
    if stripped.startswith(('"""', "'''", '"', "'")):
        return False
    if stripped.startswith(_BLOCKED_PREFIXES):
        return False
    head = stripped.split("(")[0]
    if " = " in head or head.endswith("="):
        return False
    if "(" not in stripped:
        return False
    indent = line[: len(line) - len(stripped)]
    lines[start] = f"{indent}_ = {stripped}"
    return True


def _fix_implicit_concat(lines: list[str], line_idx: int) -> bool:
    line = lines[line_idx]
    stripped = line.rstrip()
    if not stripped.endswith(('"', "'")):
        return False
    if line_idx + 1 >= len(lines):
        return False
    nxt = lines[line_idx + 1].lstrip()
    if not nxt.startswith(('"', "'")):
        return False
    if stripped.endswith("+"):
        return False
    lines[line_idx] = stripped + " +"
    return True


def _fix_unnecessary_ignore(lines: list[str], line_idx: int) -> bool:
    line = lines[line_idx]
    new_line = _TYPE_IGNORE.sub("", _PYRIGHT_IGNORE.sub("", line.rstrip()))
    if new_line == line.rstrip():
        return False
    lines[line_idx] = new_line + ("\n" if line.endswith("\n") else "")
    return True


def _diag_line(diag: dict[str, object]) -> int:
    range_obj = diag.get("range")
    if not isinstance(range_obj, dict):
        return -1
    start = range_obj.get("start")
    if not isinstance(start, dict):
        return -1
    line = start.get("line")
    return line if isinstance(line, int) else -1


def apply_fixes(diagnostics: list[dict[str, object]], repo: Path) -> int:
    by_file: dict[str, list[dict[str, object]]] = defaultdict(list)
    for diag in diagnostics:
        file = str(diag.get("file", ""))
        if not file:
            continue
        if _repo_relative(Path(file), repo) in _SKIP_FILES:
            continue
        by_file[file].append(diag)

    changed_files = 0
    for file_path, diags in by_file.items():
        path = Path(file_path)
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        sorted_diags = sorted(
            diags,
            key=_diag_line,
            reverse=True,
        )
        file_changed = False
        seen_unused: set[int] = set()
        for diag in sorted_diags:
            rule = str(diag.get("rule", ""))
            line_idx = _diag_line(diag)
            if line_idx < 0 or line_idx >= len(lines):
                continue
            if rule == "reportUnusedCallResult":
                start = _statement_start_line(lines, line_idx)
                if start in seen_unused:
                    continue
                if _fix_unused_call_result(lines, line_idx):
                    seen_unused.add(start)
                    file_changed = True
            elif rule == "reportImplicitStringConcatenation":
                file_changed |= _fix_implicit_concat(lines, line_idx)
            elif rule == "reportUnnecessaryTypeIgnoreComment":
                file_changed |= _fix_unnecessary_ignore(lines, line_idx)
        if file_changed:
            _ = path.write_text("".join(lines), encoding="utf-8")
            changed_files += 1
    return changed_files


def main() -> int:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("json_path", type=Path)
    _ = parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    payload = json.loads(args.json_path.read_text(encoding="utf-8"))
    changed = apply_fixes(payload.get("generalDiagnostics", []), args.repo)
    print(f"updated {changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
