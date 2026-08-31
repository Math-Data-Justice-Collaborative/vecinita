"""BUG-2026-08-31 — register-workspace-plugins must not bake /Users/... paths.

Symptom: workspaceOpen returned pluginPaths under /Users/bigme/... so the
engineering-memory plugin only loaded for the original developer.
Upstream: joseph-c-mcguire/spec-dev-knowledge-graph#106
Vecinita: Math-Data-Justice-Collaborative/vecinita#301
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_HOOK = _REPO / ".cursor" / "hooks" / "register-workspace-plugins.sh"
_MACHINE_LOCAL = re.compile(r"/Users/|/home/[A-Za-z0-9._-]+/")


def test_register_workspace_plugins_source_has_no_machine_local_path() -> None:
    """Tracked hook source must not embed install-time /Users/... bake-ins."""
    assert _HOOK.is_file(), f"missing {_HOOK}"
    source = _HOOK.read_text(encoding="utf-8")
    assert "resolve_plugin_dir" in source
    assert _MACHINE_LOCAL.search(source) is None, (
        "register-workspace-plugins.sh must not contain machine-local absolute "
        "paths (BUG-2026-08-31 / #301 / upstream #106)"
    )


def test_register_workspace_plugins_missing_root_returns_empty_paths(
    tmp_path: Path,
) -> None:
    """Missing EM root → fail-open empty pluginPaths (not a hard crash)."""
    env = os.environ.copy()
    env["EM_ENGINEERING_MEMORY_ROOT"] = str(tmp_path / "does-not-exist")
    proc = subprocess.run(  # noqa: S603  # trusted tracked hook under .cursor/hooks
        ["/bin/bash", str(_HOOK)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip())
    assert payload == {"pluginPaths": []}
