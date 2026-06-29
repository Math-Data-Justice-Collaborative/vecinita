#!/usr/bin/env python3
"""Print unit-test coverage grouped by packages/ apps (Python + TypeScript)."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE_DIR = ROOT / "coverage"
DEFAULT_LINE_THRESHOLD = 95.0
DEFAULT_BRANCH_THRESHOLD = 95.0


@dataclass(frozen=True)
class CliOptions:
    coverage_dir: Path
    enforce: bool
    line_threshold: float
    branch_threshold: float


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

    @property
    def branch_pct(self) -> float:
        if self.branches_total == 0:
            return 100.0
        return 100.0 * self.branches_covered / self.branches_total


def _component_from_path(relative_path: str) -> str:
    parts = Path(relative_path).parts
    if len(parts) >= 2 and parts[0] in {"packages", "apps"}:
        return f"{parts[0]}/{parts[1]}"
    return relative_path


def _normalize_path(path: str) -> str:
    normalized = Path(path)
    if normalized.is_absolute():
        with contextlib.suppress(ValueError):
            normalized = normalized.relative_to(ROOT)
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
        return cast("dict[str, object]", value)
    return {}


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_python_rows(coverage_dir: Path) -> list[CoverageRow]:
    report_path = coverage_dir / "python.json"
    if not report_path.is_file():
        print(f"warning: missing {_display_path(report_path)}", file=sys.stderr)
        return []

    payload = _as_mapping(cast("object", json.loads(report_path.read_text(encoding="utf-8"))))
    grouped: dict[str, dict[str, int]] = {}

    files = _as_mapping(payload.get("files"))
    for raw_path, file_data in files.items():
        rel_path = _normalize_path(raw_path)
        component = _component_from_path(rel_path)
        summary = _as_mapping(_as_mapping(file_data).get("summary"))
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


def _load_typescript_row(coverage_dir: Path, app: str) -> CoverageRow | None:
    report_path = coverage_dir / app / "coverage-summary.json"
    if not report_path.is_file():
        print(f"warning: missing {_display_path(report_path)}", file=sys.stderr)
        return None

    payload = _as_mapping(cast("object", json.loads(report_path.read_text(encoding="utf-8"))))
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
        print(f"{row.component:<40} {line_label:>12} {branch_label:>12} {row.line_pct:>7.1f}%")

    total = _aggregate(rows)
    line_label = f"{total.lines_covered}/{total.lines_total}"
    if total.branches_total:
        branch_label = f"{total.branches_covered}/{total.branches_total}"
    else:
        branch_label = "n/a"
    print("-" * 76)
    print(f"{total.component:<40} {line_label:>12} {branch_label:>12} {total.line_pct:>7.1f}%")
    print()


def _below_threshold(
    row: CoverageRow,
    *,
    line_threshold: float,
    branch_threshold: float,
) -> list[str]:
    failures: list[str] = []
    if row.line_pct < line_threshold:
        failures.append(
            f"{row.component}: line coverage {row.line_pct:.1f}% below {line_threshold:.0f}%"
        )
    if row.branches_total > 0 and row.branch_pct < branch_threshold:
        failures.append(
            f"{row.component}: branch coverage {row.branch_pct:.1f}% below {branch_threshold:.0f}%"
        )
    return failures


def _parse_args(argv: list[str] | None = None) -> CliOptions:
    parser = argparse.ArgumentParser(
        description="Print per-component unit test coverage summary.",
    )
    parser.add_argument(
        "--coverage-dir",
        type=Path,
        default=DEFAULT_COVERAGE_DIR,
        help="Directory containing python.json and frontend coverage summaries.",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Exit 1 when any component is below line or branch thresholds.",
    )
    parser.add_argument(
        "--line-threshold",
        type=float,
        default=DEFAULT_LINE_THRESHOLD,
        help="Minimum line coverage percentage per component (default: 95).",
    )
    parser.add_argument(
        "--branch-threshold",
        type=float,
        default=DEFAULT_BRANCH_THRESHOLD,
        help="Minimum branch coverage percentage per component (default: 95).",
    )
    parsed = parser.parse_args(argv)
    coverage_dir = cast("Path", parsed.coverage_dir)
    enforce = cast("bool", parsed.enforce)
    line_threshold = cast("float", parsed.line_threshold)
    branch_threshold = cast("float", parsed.branch_threshold)
    return CliOptions(
        coverage_dir=coverage_dir,
        enforce=enforce,
        line_threshold=line_threshold,
        branch_threshold=branch_threshold,
    )


def main(argv: list[str] | None = None) -> int:
    options = _parse_args(argv)
    coverage_dir = options.coverage_dir

    python_rows = _load_python_rows(coverage_dir)
    typescript_rows = [
        row
        for app in ("chat-rag-frontend", "data-management-frontend")
        if (row := _load_typescript_row(coverage_dir, app)) is not None
    ]

    print()
    print("Unit test coverage summary")
    print("=" * 76)
    print("HTML reports: htmlcov/ (Python), coverage/<app>/ (TypeScript)")
    print()

    _print_section("Python (packages + backend apps)", python_rows)
    _print_section("TypeScript (frontend apps)", typescript_rows)

    all_rows = python_rows + typescript_rows
    if all_rows:
        _print_section("Combined", all_rows)

    if not python_rows and not typescript_rows:
        print("No coverage reports found.", file=sys.stderr)
        return 1

    if options.enforce:
        failures: list[str] = []
        for row in all_rows:
            failures.extend(
                _below_threshold(
                    row,
                    line_threshold=options.line_threshold,
                    branch_threshold=options.branch_threshold,
                )
            )
        if failures:
            print("Coverage gate failed:", file=sys.stderr)
            for message in failures:
                print(message, file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
