#!/usr/bin/env python3
"""Print unit-test coverage grouped by packages/ apps (Python + TypeScript)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[2]
COVERAGE_DIR = ROOT / "coverage"


@dataclass(frozen=True)
class CoverageRow:
    component: str
    lines_total: int
    lines_covered: int
    branches_total: int
    branches_covered: int

    @property
    def line_pct(self) -> float:
        if self.lines_total == 0:
            return 100.0
        return 100.0 * self.lines_covered / self.lines_total


def _component_from_path(relative_path: str) -> str:
    parts = Path(relative_path).parts
    if len(parts) >= 2 and parts[0] in {"packages", "apps"}:
        return f"{parts[0]}/{parts[1]}"
    return relative_path


def _normalize_path(path: str) -> str:
    normalized = Path(path)
    if normalized.is_absolute():
        try:
            normalized = normalized.relative_to(ROOT)
        except ValueError:
            pass
    return normalized.as_posix()


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    return default


def _as_mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return cast(dict[str, object], value)
    return {}


def _load_python_rows() -> list[CoverageRow]:
    report_path = COVERAGE_DIR / "python.json"
    if not report_path.is_file():
        print(f"warning: missing {report_path.relative_to(ROOT)}", file=sys.stderr)
        return []

    payload = _as_mapping(cast(object, json.loads(report_path.read_text(encoding="utf-8"))))
    grouped: dict[str, dict[str, int]] = {}

    files = _as_mapping(payload.get("files"))
    for raw_path, file_data in files.items():
        rel_path = _normalize_path(raw_path)
        component = _component_from_path(rel_path)
        summary = _as_mapping(file_data.get("summary"))
        bucket = grouped.setdefault(
            component,
            {
                "lines_total": 0,
                "lines_covered": 0,
                "branches_total": 0,
                "branches_covered": 0,
            },
        )
        bucket["lines_total"] += _as_int(summary.get("num_statements"))
        bucket["lines_covered"] += _as_int(summary.get("covered_lines"))
        bucket["branches_total"] += _as_int(summary.get("num_branches"))
        bucket["branches_covered"] += _as_int(summary.get("covered_branches"))

    return [
        CoverageRow(
            component=component,
            lines_total=values["lines_total"],
            lines_covered=values["lines_covered"],
            branches_total=values["branches_total"],
            branches_covered=values["branches_covered"],
        )
        for component, values in sorted(grouped.items())
    ]


def _metric_block(block: object) -> tuple[int, int]:
    mapping = _as_mapping(block)
    total = _as_int(mapping.get("total"))
    covered = _as_int(mapping.get("covered"))
    return total, covered


def _load_typescript_row(app: str) -> CoverageRow | None:
    report_path = COVERAGE_DIR / app / "coverage-summary.json"
    if not report_path.is_file():
        print(f"warning: missing {report_path.relative_to(ROOT)}", file=sys.stderr)
        return None

    payload = _as_mapping(cast(object, json.loads(report_path.read_text(encoding="utf-8"))))
    total = _as_mapping(payload.get("total"))
    lines_total, lines_covered = _metric_block(total.get("lines"))
    branches_total, branches_covered = _metric_block(total.get("branches"))
    return CoverageRow(
        component=f"apps/{app}",
        lines_total=lines_total,
        lines_covered=lines_covered,
        branches_total=branches_total,
        branches_covered=branches_covered,
    )


def _aggregate(rows: list[CoverageRow]) -> CoverageRow:
    return CoverageRow(
        component="TOTAL",
        lines_total=sum(row.lines_total for row in rows),
        lines_covered=sum(row.lines_covered for row in rows),
        branches_total=sum(row.branches_total for row in rows),
        branches_covered=sum(row.branches_covered for row in rows),
    )


def _print_section(title: str, rows: list[CoverageRow]) -> None:
    if not rows:
        return

    print(title)
    print(f"{'Component':<40} {'Lines':>12} {'Branches':>12} {'Line %':>8}")
    print("-" * 76)
    for row in rows:
        line_label = f"{row.lines_covered}/{row.lines_total}"
        if row.branches_total:
            branch_label = f"{row.branches_covered}/{row.branches_total}"
        else:
            branch_label = "n/a"
        print(
            f"{row.component:<40} {line_label:>12} {branch_label:>12} "
            f"{row.line_pct:>7.1f}%"
        )

    total = _aggregate(rows)
    line_label = f"{total.lines_covered}/{total.lines_total}"
    if total.branches_total:
        branch_label = f"{total.branches_covered}/{total.branches_total}"
    else:
        branch_label = "n/a"
    print("-" * 76)
    print(
        f"{total.component:<40} {line_label:>12} {branch_label:>12} "
        f"{total.line_pct:>7.1f}%"
    )
    print()


def main() -> int:
    python_rows = _load_python_rows()
    typescript_rows = [
        row
        for app in ("chat-rag-frontend", "data-management-frontend")
        if (row := _load_typescript_row(app)) is not None
    ]

    print("")
    print("Unit test coverage summary")
    print("=" * 76)
    print("HTML reports: htmlcov/ (Python), coverage/<app>/ (TypeScript)")
    print("")

    _print_section("Python (packages + backend apps)", python_rows)
    _print_section("TypeScript (frontend apps)", typescript_rows)

    all_rows = python_rows + typescript_rows
    if all_rows:
        _print_section("Combined", all_rows)

    if not python_rows and not typescript_rows:
        print("No coverage reports found.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
