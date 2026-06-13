"""Unit tests for the per-component coverage gate (ADR-019, AC-Q2).

T32.1 (red): --enforce must fail when fixture coverage is below 95% line or branch.
Implementation lands in T32.2 (print_unit_coverage_summary.py).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_SCRIPT = ROOT / "scripts" / "test" / "print_unit_coverage_summary.py"
THRESHOLD = 95.0


def _write_python_coverage(
    coverage_dir: Path,
    *,
    component_path: str,
    lines_total: int,
    lines_covered: int,
    branches_total: int,
    branches_covered: int,
) -> None:
    coverage_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "files": {
            component_path: {
                "summary": {
                    "num_statements": lines_total,
                    "covered_lines": lines_covered,
                    "num_branches": branches_total,
                    "covered_branches": branches_covered,
                }
            }
        }
    }
    (coverage_dir / "python.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def _run_summary(
    coverage_dir: Path,
    *,
    enforce: bool,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SUMMARY_SCRIPT),
        "--coverage-dir",
        str(coverage_dir),
        "--line-threshold",
        str(int(THRESHOLD)),
        "--branch-threshold",
        str(int(THRESHOLD)),
    ]
    if enforce:
        command.append("--enforce")
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_enforce_fails_when_line_coverage_below_threshold(tmp_path: Path) -> None:
    """AC-Q2: --enforce exits 1 when any component line coverage is below 95%."""
    _write_python_coverage(
        tmp_path,
        component_path="packages/tagging/tagging/core.py",
        lines_total=100,
        lines_covered=94,
        branches_total=20,
        branches_covered=20,
    )

    result = _run_summary(tmp_path, enforce=True)

    assert result.returncode == 1
    assert "packages/tagging" in result.stderr.lower() or "packages/tagging" in result.stdout


def test_enforce_fails_when_branch_coverage_below_threshold(tmp_path: Path) -> None:
    """AC-Q2: --enforce exits 1 when any component branch coverage is below 95%."""
    _write_python_coverage(
        tmp_path,
        component_path="packages/rag/rag/engine.py",
        lines_total=100,
        lines_covered=96,
        branches_total=100,
        branches_covered=94,
    )

    result = _run_summary(tmp_path, enforce=True)

    assert result.returncode == 1
    assert "packages/rag" in result.stderr.lower() or "packages/rag" in result.stdout


def test_enforce_passes_when_all_components_meet_thresholds(tmp_path: Path) -> None:
    """Synthetic fixture at 95% line + branch exits 0 with --enforce."""
    _write_python_coverage(
        tmp_path,
        component_path="packages/shared-schemas/shared_schemas/models.py",
        lines_total=100,
        lines_covered=95,
        branches_total=100,
        branches_covered=95,
    )

    result = _run_summary(tmp_path, enforce=True)

    assert result.returncode == 0


def test_enforce_not_required_without_flag(tmp_path: Path) -> None:
    """Without --enforce, low coverage still prints a summary and exits 0."""
    _write_python_coverage(
        tmp_path,
        component_path="packages/tagging/tagging/core.py",
        lines_total=100,
        lines_covered=50,
        branches_total=20,
        branches_covered=10,
    )

    result = _run_summary(tmp_path, enforce=False)

    assert result.returncode == 0
