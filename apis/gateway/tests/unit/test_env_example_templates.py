"""Contract checks for committed env example templates (C4b, C7)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_C4B = "Canonical environment catalog: repo root .env.example"

# Assignment RHS that look like real secrets (not placeholders).
_SECRET_LIKE = re.compile(
    r"(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}|"
    r"sk-[A-Za-z0-9]{20,}|"
    r"ghp_[A-Za-z0-9]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{10,})"
)


def _iter_example_env_files() -> list[Path]:
    skip_parts = {"node_modules", ".venv", "venv", "dist", "build", ".git"}
    paths = sorted(p for p in _REPO_ROOT.rglob(".env.example") if skip_parts.isdisjoint(p.parts))
    local = _REPO_ROOT / ".env.local.example"
    if local.is_file():
        paths.append(local)
    return paths


def _is_root_canonical(path: Path) -> bool:
    return path.name == ".env.example" and path.parent == _REPO_ROOT


@pytest.mark.parametrize(
    "path", _iter_example_env_files(), ids=lambda p: str(p.relative_to(_REPO_ROOT))
)
def test_subsidiary_pointer_substring_first_40_lines(path: Path) -> None:
    """C4b: subsidiary templates and pointer `.env.local.example` include the catalog substring."""
    if _is_root_canonical(path):
        return
    lines = path.read_text(encoding="utf-8").splitlines()[:40]
    head = "\n".join(lines)
    assert _C4B in head, f"missing C4b pointer in first 40 lines: {path.relative_to(_REPO_ROOT)}"


@pytest.mark.parametrize(
    "path", _iter_example_env_files(), ids=lambda p: str(p.relative_to(_REPO_ROOT))
)
def test_no_secret_shaped_assignment_values(path: Path) -> None:
    """C7: block obvious secret material in tracked example env files."""
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        _, rhs = stripped.split("=", 1)
        rhs = rhs.strip().strip('"').strip("'")
        if not rhs:
            continue
        if _SECRET_LIKE.search(rhs):
            pytest.fail(f"secret-like value in {path.relative_to(_REPO_ROOT)}:{lineno}")
