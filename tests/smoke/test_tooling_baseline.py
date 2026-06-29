"""06-tech-tooling: verify pytest discovery and dev toolchain imports."""

from __future__ import annotations

import importlib.util


def test_pytest_runs() -> None:
    """Pytest collects and runs a trivial test."""
    assert True


def test_ruff_and_basedpyright_available() -> None:
    """The ruff and basedpyright dev tools are importable in the environment."""
    assert importlib.util.find_spec("ruff") is not None
    assert importlib.util.find_spec("basedpyright") is not None
