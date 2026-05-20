"""06-tech-tooling: verify pytest discovery and dev toolchain imports."""

from __future__ import annotations


def test_pytest_runs() -> None:
    assert True


def test_ruff_and_pyright_available() -> None:
    import importlib.util

    assert importlib.util.find_spec("ruff") is not None
    assert importlib.util.find_spec("pyright") is not None
