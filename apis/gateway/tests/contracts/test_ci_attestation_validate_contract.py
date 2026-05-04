"""Contract tests for scripts/ci/ci_attestation_validate.py (feature 019)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.contract]

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "ci_attestation_validate.py"
_FIXTURES = _REPO_ROOT / "specs" / "019-contract-ci-json-gate" / "fixtures"


def _run(
    manifest: Path,
    attestation: Path,
    *,
    max_age_hours: float = 1_000_000.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--manifest",
            str(manifest),
            "--attestation",
            str(attestation),
            "--max-age-hours",
            str(max_age_hours),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _copy_pair(manifest_name: str, attestation_name: str, tmp: Path) -> tuple[Path, Path]:
    m = tmp / "required-checks.json"
    a = tmp / "ci-attestation.json"
    shutil.copy(_FIXTURES / manifest_name, m)
    shutil.copy(_FIXTURES / attestation_name, a)
    return m, a


def _touch_fresh_attestation(attestation: Path) -> None:
    data = json.loads(attestation.read_text(encoding="utf-8"))
    data["generated_at"] = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    attestation.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_valid_manifest_and_attestation_passes() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-valid-minimal.json", "attestation-valid.json", tmp)
        _touch_fresh_attestation(a)
        proc = _run(m, a)
        assert proc.returncode == 0, proc.stderr


def test_manifest_duplicate_ids_emits_schema() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-invalid-duplicate-ids.json", "attestation-valid.json", tmp)
        _touch_fresh_attestation(a)
        proc = _run(m, a)
        assert proc.returncode != 0
        assert "schema" in proc.stderr


def test_manifest_empty_checks_emits_schema() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-invalid-empty-checks.json", "attestation-valid.json", tmp)
        _touch_fresh_attestation(a)
        proc = _run(m, a)
        assert proc.returncode != 0
        assert "schema" in proc.stderr


def test_stale_attestation_emits_staleness() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-valid-minimal.json", "attestation-stale.json", tmp)
        proc = _run(m, a, max_age_hours=1.0)
        assert proc.returncode != 0
        assert "staleness" in proc.stderr


def test_incomplete_attestation_emits_incomplete_manifest() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-valid-minimal.json", "attestation-incomplete.json", tmp)
        _touch_fresh_attestation(a)
        proc = _run(m, a)
        assert proc.returncode != 0
        assert "incomplete_manifest" in proc.stderr


def test_failed_check_emits_failed_check() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-valid-minimal.json", "attestation-failed-check.json", tmp)
        _touch_fresh_attestation(a)
        proc = _run(m, a)
        assert proc.returncode != 0
        assert "failed_check" in proc.stderr


def test_non_utf8_attestation_emits_io_or_parse() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-valid-minimal.json", "attestation-valid.json", tmp)
        a.write_bytes(b"\xff\xfe{\x00")
        proc = _run(m, a)
        assert proc.returncode != 0
        assert "io_or_parse" in proc.stderr


def test_unknown_top_level_attestation_property_emits_schema() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        m, a = _copy_pair("manifest-valid-minimal.json", "attestation-valid.json", tmp)
        data = json.loads((_FIXTURES / "attestation-valid.json").read_text(encoding="utf-8"))
        data["extra_field"] = 1
        data["generated_at"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
        a.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        proc = _run(m, a)
        assert proc.returncode != 0
        assert "schema" in proc.stderr
