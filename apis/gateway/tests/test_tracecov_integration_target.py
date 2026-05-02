"""Unit tests for TraceCov target selection in ``tests/integration/conftest.py``."""

from __future__ import annotations

import pytest

from tests.integration.conftest import _resolve_tracecov_target

pytestmark = pytest.mark.unit


def test_resolve_tracecov_target_gateway_only():
    assert (
        _resolve_tracecov_target(
            ["tests/integration/test_api_schema_schemathesis.py::test_gateway_openapi_schema"]
        )
        == "gateway"
    )


def test_resolve_tracecov_target_agent_only():
    assert (
        _resolve_tracecov_target(
            [
                "tests/integration/test_agent_api_schema_schemathesis.py::test_agent_openapi_stable_operations"
            ]
        )
        == "agent"
    )


def test_resolve_tracecov_target_data_management_only():
    assert (
        _resolve_tracecov_target(
            [
                "tests/integration/test_data_management_api_schema_schemathesis.py::test_data_management_openapi_stable"
            ]
        )
        == "data-management"
    )


def test_resolve_tracecov_target_mixed_two_disables_tracecov():
    assert (
        _resolve_tracecov_target(
            [
                "tests/integration/test_api_schema_schemathesis.py::a",
                "tests/integration/test_agent_api_schema_schemathesis.py::b",
            ]
        )
        is None
    )


def test_resolve_tracecov_target_unrelated():
    assert _resolve_tracecov_target(["tests/unit/test_foo.py::t"]) is None
