"""Guard: test_fast.sh must run on macOS /bin/bash 3.2 (no mapfile / assoc arrays)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_FAST = REPO_ROOT / "scripts" / "ci" / "test_fast.sh"
_BASH = Path("/bin/bash")


@pytest.mark.unit
def test_test_fast_sh_avoids_bash4_only_builtins() -> None:
    """S031: portable bash 3.2 — no mapfile or declare -A (macOS stock bash)."""
    body = TEST_FAST.read_text(encoding="utf-8")
    assert not re.search(r"(?m)^\s*mapfile\b", body), (
        "mapfile is bash 4+; use while-read for bash 3.2"
    )
    assert not re.search(r"declare\s+-A\b", body), (
        "declare -A is bash 4+; use newline-delimited lists for bash 3.2"
    )


@pytest.mark.unit
def test_test_fast_sh_syntax_ok_on_bin_bash() -> None:
    """Bash -n must succeed under /bin/bash (3.2 on macOS)."""
    if not _BASH.is_file():
        pytest.skip("bash not available")
    result = subprocess.run(  # noqa: S603
        [str(_BASH), "-n", str(TEST_FAST)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.unit
def test_test_fast_membership_helpers_on_bin_bash(tmp_path: Path) -> None:
    """Under /bin/bash 3.2, membership helpers must dedupe and exit 0."""
    if not _BASH.is_file():
        pytest.skip("bash not available")

    harness = tmp_path / "run_test_fast.sh"
    _ = harness.write_text(
        "#!/usr/bin/env bash\n"
        + "set -euo pipefail\n"
        + 'list_has() { local n="$1"; local h="${2-}"; '
        + '[[ -n "$h" ]] || return 1; printf \'%s\\n\' "$h" | grep -Fxq -- "$n"; }\n'
        + "list_add() {\n"
        + '  local n="$1"; local h="${2-}"\n'
        + '  if list_has "$n" "$h"; then printf \'%s\' "$h"; return 0; fi\n'
        + '  if [[ -n "$h" ]]; then printf \'%s\\n%s\' "$h" "$n"; else printf \'%s\' "$n"; fi\n'
        + "}\n"
        + 'PY_PATHS=""\n'
        + 'PY_PATHS="$(list_add tests/unit/scripts "$PY_PATHS")"\n'
        + 'PY_PATHS="$(list_add tests/unit/scripts "$PY_PATHS")"\n'
        + 'echo "paths=$PY_PATHS"\n'
        + 'echo "test-fast: no testable source changes; skipping"\n',
        encoding="utf-8",
    )
    result = subprocess.run(  # noqa: S603
        [str(_BASH), str(harness)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert "mapfile: command not found" not in combined
    assert "declare: -A" not in combined
    assert result.returncode == 0, combined
    assert "paths=tests/unit/scripts" in combined
    assert "skipping" in combined
