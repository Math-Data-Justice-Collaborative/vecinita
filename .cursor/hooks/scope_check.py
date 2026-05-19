"""Cursor preToolUse hook: advisory check that new files map to approved components.

Reads the file path from stdin JSON, checks against the component list in docs/spec.md,
and returns advisory context. Never blocks — always exits 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath

APPROVED_COMPONENTS: dict[str, str] = {
    "src/app.py": "Modal App (F5/F6/F8/F9)",
    "src/pipeline.py": "Pipeline Orchestrator (F5)",
    "src/weights.py": "Weight Manager (F6)",
    "src/config.py": "Config Module (F5/F7)",
    "src/output.py": "Output Packaging (F5)",
    "src/rfdiffusion_stage.py": "RFdiffusion Stage (F1)",
    "src/proteinmpnn_stage.py": "ProteinMPNN Stage (F2)",
    "src/rf2_stage.py": "TCR RF2 Stage (F4 only, ADR-007)",
    "src/finetune": "Fine-Tune Module (F8)",
    "tests": "Test Suite",
    "docs": "Documentation",
    ".cursor": "Cursor Tooling",
    ".github": "CI/CD",
}


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def match_component(rel_path: str) -> str | None:
    posix = PurePosixPath(rel_path)
    path_str = str(posix)
    for prefix, component in APPROVED_COMPONENTS.items():
        if path_str == prefix or path_str.startswith(prefix + "/"):
            return component
    return None


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
    if repo is None:
        print("{}")
        return 0

    try:
        rel = file_path.resolve().relative_to(repo.resolve())
    except ValueError:
        print("{}")
        return 0

    rel_str = str(rel).replace("\\", "/")
    component = match_component(rel_str)

    if component:
        result = {"additional_context": f"[scope-check] File maps to: {component}"}
    else:
        result = {
            "additional_context": (
                f"[scope-check] WARNING: '{rel_str}' does not map to any approved "
                "component in docs/spec.md. Verify this file is in scope (F1-F9) "
                "or raise [Scope Drift]."
            )
        }

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
