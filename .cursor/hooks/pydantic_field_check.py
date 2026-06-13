"""Cursor afterFileEdit hook: flag invalid Pydantic Field() metadata patterns.

Detects validate_default misuse and PEP 695 type aliases with Field() metadata in edited
Python files under apps/, packages/, tests/, and infra/.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_PY_DIRS = frozenset({"apps", "packages", "tests", "infra"})

_VALIDATE_DEFAULT = re.compile(r"\bvalidate_default\s*=")
_TYPE_ALIAS_FIELD = re.compile(r"^\s*type\s+\w+\s*=.*\bField\s*\(", re.MULTILINE)
_UNION_FIELD = re.compile(
    r"^\s*\w+\s*:\s*[^=\n]*\|\s*[^=\n]*=\s*Field\s*\(",
    re.MULTILINE,
)


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def should_check(repo: Path, file_path: Path) -> bool:
    if file_path.suffix != ".py":
        return False
    try:
        rel = file_path.resolve().relative_to(repo.resolve())
    except ValueError:
        return False
    parts = rel.parts
    return bool(parts) and parts[0] in _PY_DIRS


def scan_source(source: str) -> list[str]:
    findings: list[str] = []
    if _VALIDATE_DEFAULT.search(source):
        findings.append(
            "validate_default= in Field() has no effect in Pydantic v2; "
            "use Annotated metadata or @field_validator instead "
            "(see .cursor/rules/pydantic-field-metadata.mdc)."
        )
    if _TYPE_ALIAS_FIELD.search(source):
        findings.append(
            "PEP 695 `type` alias with Field() metadata triggers "
            "UnsupportedFieldAttributeWarning; use TypeAlias + Annotated instead."
        )
    if _UNION_FIELD.search(source):
        findings.append(
            "Field() on a union-typed model attribute may trigger "
            "UnsupportedFieldAttributeWarning; prefer a non-union type or "
            "TypeAlias + Annotated (see pydantic-field-metadata.mdc)."
        )
    return findings


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    raw = payload.get("filePath") or payload.get("file_path") or ""
    if not raw:
        print("{}")
        return 0

    file_path = Path(raw)
    repo = find_repo_root(file_path)
    if repo is None or not should_check(repo, file_path):
        print("{}")
        return 0

    try:
        source = file_path.read_text(encoding="utf-8")
    except OSError:
        print("{}")
        return 0

    findings = scan_source(source)
    if not findings:
        print("{}")
        return 0

    body = "\n".join(f"- {item}" for item in findings)
    result = {"additional_context": f"[pydantic-field] Review Field() usage:\n{body}"}
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
