"""Regression: ``pact-python`` must be declared under ``[project.optional-dependencies].ci``.

Merge-blocking backend workflows and root ``make ci`` run ``uv sync --frozen --extra ci``,
which installs **project optional extras** named ``ci`` only. UV ``[dependency-groups]`` are
not selected by ``--extra ci``.

Pytest imports every test module during collection **before** ``-m`` marker deselection.
Modules under ``tests/pact/`` use ``from pact import Pact`` at import time; if ``pact-python``
is missing from the frozen CI environment, collection fails with ``ModuleNotFoundError`` even
when those tests would be deselected for a given marker expression.

See ``TESTING_DOCUMENTATION.md`` (backend ``vecinita[ci]`` vs dependency-groups).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.contract]

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = BACKEND_ROOT / "pyproject.toml"


def _parse_pyproject(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    try:
        import tomllib as _toml
    except ModuleNotFoundError:
        import tomli as _toml  # type: ignore[import-not-found,no-redef]

    return _toml.loads(raw)


def test_ci_extra_lists_pact_python_for_pytest_collection() -> None:
    assert PYPROJECT.is_file(), f"Missing backend pyproject at {PYPROJECT}"
    data = _parse_pyproject(PYPROJECT)
    ci = data.get("project", {}).get("optional-dependencies", {}).get("ci")
    assert isinstance(ci, list), "pyproject.toml [project.optional-dependencies].ci must be a list"
    assert any(isinstance(spec, str) and spec.strip().startswith("pact-python") for spec in ci), (
        "pact-python must appear in [project.optional-dependencies].ci: CI uses "
        "`uv sync --frozen --extra ci` (not UV dependency-groups alone); pytest imports "
        "tests/pact/*.py during collection before marker filters apply."
    )
