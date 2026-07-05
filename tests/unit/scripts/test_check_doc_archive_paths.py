"""Guard against stale references to docs moved into S000 archive."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CHECK_SCRIPT = REPO_ROOT / "scripts" / "check_doc_archive_paths.sh"
_BASH = Path("/bin/bash")


def test_no_stale_doc_archive_path_references() -> None:
    if not _BASH.is_file():
        return
    result = subprocess.run(  # noqa: S603
        [str(_BASH), str(CHECK_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
