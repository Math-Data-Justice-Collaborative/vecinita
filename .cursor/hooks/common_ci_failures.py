"""Cursor hooks: catch common CI failure patterns before they reach GitHub Actions.

afterFileEdit: advisory ruff/eslint checks + static footgun detectors.
preToolUse (Shell): push reminder for checks that auto-fix hooks cannot enforce.

Always exits 0; failures are injected via additional_context.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_paths import (
    find_repo_root,
    frontend_format_lint_workspace,
    python_typecheck_target,
    relative_parts,
)
from repo_make_lock import repo_lock

_MIGRATION_DIR = ("apps", "database", "alembic", "versions")
_EV002_SCHEMA_TEST = Path("tests/integration/test_ev002_schema.py")
_INLINE_IMPORT = re.compile(r"^    (?:from \S+ import|import \S+)", re.MULTILINE)
_TEST_FUNCTION = re.compile(r"^def test_\w+\(", re.MULTILINE)
_RESOLVE_RUNTIME_OR_BUG = re.compile(
    r"judge\s+is\s+None\s+or\s+llm\s+is\s+None",
)
_MIGRATION_REVISION = re.compile(r"^(\d{8}_\d{4})_", re.MULTILINE)

_PUSH_TRIGGERS = ("git push", "gh pr create")

_PUSH_REMINDER = """\
[common-ci-failures] Fast checks on agent stop: make check-fast + make test-fast.
Pre-push (Husky): make check-fast + make test-fast. Before PR: make ci-push.
Opt-in medium pre-push: VECINITA_MEDIUM_PRE_PUSH=1. Opt-in full: VECINITA_FULL_PRE_PUSH=1. Skip: VECINITA_SKIP_PRE_PUSH=1.
Also verify before push:
  1. Frontend tests: eslint unused imports in apps/*/src/test/*.test.tsx
  2. Python tests: top-level imports only (ruff PLC0415); drop unused fixtures (ARG001)
  3. New Alembic migration: update tests/integration/test_ev002_schema.py head assertion
  4. eval_service _resolve_eval_runtime: factory fallback only when BOTH judge and llm are None
After push: bash scripts/ci/watch_github_ci.sh [branch] (on main: ci.yml + deploy-preflight.yml)"""


def migration_revision_from_path(path: Path) -> str | None:
    """Return Alembic revision prefix from a versions/*.py filename."""
    match = _MIGRATION_REVISION.match(path.name)
    return match.group(1) if match else None


def check_migration_head_drift(repo: Path, migration_path: Path) -> str | None:
    """Warn when a new migration may require updating the EV-002 schema head test."""
    revision = migration_revision_from_path(migration_path)
    if revision is None:
        return None
    schema_test = repo / _EV002_SCHEMA_TEST
    if not schema_test.is_file():
        return (
            f"[common-ci-failures] New migration {revision}: add or update "
            f"{_EV002_SCHEMA_TEST} to assert the Alembic head revision."
        )
    content = schema_test.read_text(encoding="utf-8")
    if revision in content:
        return None
    return (
        f"[common-ci-failures] New migration {revision}: update "
        f"{_EV002_SCHEMA_TEST}::test_alembic_head_includes_ev002_migration "
        f"to expect head {revision} in current/heads stdout while keeping "
        f"20260701_0006 (EV-002) in history."
    )


def check_test_inline_imports(path: Path, content: str) -> str | None:
    """Flag imports indented inside test modules (ruff PLC0415)."""
    parts = path.parts
    if "tests" not in parts or not path.name.startswith("test_") or path.suffix != ".py":
        return None
    if "def test_" not in content:
        return None
    for match in _TEST_FUNCTION.finditer(content):
        start = match.end()
        next_def = _TEST_FUNCTION.search(content, start)
        block = content[start : next_def.start() if next_def else len(content)]
        if _INLINE_IMPORT.search(block):
            return (
                f"[common-ci-failures] {path}: move test imports to module top-level "
                f"(ruff PLC0415). CI rejects indented imports inside test functions."
            )
    return None


def check_eval_runtime_factory_guard(path: Path, content: str) -> str | None:
    """Catch regression where injected judges are dropped when llm is None."""
    if path.name != "eval_service.py":
        return None
    if _RESOLVE_RUNTIME_OR_BUG.search(content):
        return (
            "[common-ci-failures] eval_service._resolve_eval_runtime uses "
            "`judge is None or llm is None` — that replaces injected MockEvalJudge "
            "when llm is absent (UJ-039 faithfulness null). Use "
            "`judge is None and llm is None` for factory fallback."
        )
    return None


def analyze_static_patterns(repo: Path, file_path: Path) -> list[str]:
    """Fast content checks for known CI footguns."""
    messages: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return messages

    parts = relative_parts(repo, file_path)
    if parts and parts[: len(_MIGRATION_DIR)] == _MIGRATION_DIR:
        note = check_migration_head_drift(repo, file_path)
        if note:
            messages.append(note)

    inline = check_test_inline_imports(file_path, content)
    if inline:
        messages.append(inline)

    runtime = check_eval_runtime_factory_guard(file_path, content)
    if runtime:
        messages.append(runtime)

    return messages


def run_ruff_check(repo: Path, target: Path) -> str | None:
    """Run ruff check on a single file; return summary when it fails."""
    try:
        proc = subprocess.run(
            ["uv", "run", "ruff", "check", str(target)],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0:
        return None
    output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip())
    return output or None


def run_ruff_format_check(repo: Path, target: Path) -> str | None:
    """Run ruff format --check on a single file."""
    try:
        proc = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", str(target)],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0:
        return None
    output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip())
    return output or None


def run_eslint_file(repo: Path, workspace: str, target: Path) -> str | None:
    """Run eslint on one frontend source file (catches unused imports)."""
    parts = relative_parts(repo, target)
    if not parts or len(parts) < 2:
        return None
    workspace_root = repo / parts[0] / parts[1]
    try:
        rel_str = target.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return None
    cmd = [
        "bash",
        "scripts/npm_with_lock.sh",
        "bash",
        "-eu",
        "-o",
        "pipefail",
        "-c",
        f"npm exec -w {workspace} -- eslint {rel_str}",
    ]
    try:
        with repo_lock(repo, "make-hooks", exclusive=True, blocking=False) as acquired:
            if not acquired:
                return None
            proc = subprocess.run(
                cmd,
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=120,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0:
        return None
    output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip())
    return output or None


def handle_after_file_edit(payload: dict[str, object]) -> dict[str, str]:
    """Run scoped CI failure checks for an edited file."""
    raw = payload.get("filePath") or payload.get("file_path") or ""
    if not isinstance(raw, str) or not raw:
        return {}

    file_path = Path(raw)
    repo = find_repo_root(file_path)
    if repo is None:
        return {}

    messages = analyze_static_patterns(repo, file_path)

    py_target = python_typecheck_target(repo, file_path)
    if py_target is not None:
        ruff = run_ruff_check(repo, py_target)
        if ruff:
            messages.append(f"[ruff check] Non-auto-fixable lint on {py_target.name}:\n{ruff}")
        fmt = run_ruff_format_check(repo, py_target)
        if fmt:
            messages.append(f"[ruff format] Would reformat {py_target.name}:\n{fmt}")

    workspace = frontend_format_lint_workspace(repo, file_path)
    if workspace is not None and "/test/" in file_path.as_posix():
        eslint = run_eslint_file(repo, workspace, file_path.resolve())
        if eslint:
            messages.append(f"[eslint] {workspace} test file:\n{eslint}")

    if not messages:
        return {}
    return {"additional_context": "\n\n".join(messages)}


def handle_pre_tool_use(payload: dict[str, object]) -> dict[str, str]:
    """Remind about common CI checks before push/PR commands."""
    command = payload.get("command") or payload.get("input") or ""
    if not isinstance(command, str) or not command:
        return {}
    if any(trigger in command for trigger in _PUSH_TRIGGERS):
        return {"additional_context": _PUSH_REMINDER}
    return {}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    raw_path = payload.get("filePath") or payload.get("file_path") or ""
    command = payload.get("command") or payload.get("input") or ""

    if isinstance(raw_path, str) and raw_path:
        result = handle_after_file_edit(payload)
    elif isinstance(command, str) and command:
        result = handle_pre_tool_use(payload)
    else:
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
