"""Contract tests for impacted-suite routing policy (feature 017)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.contract]

_SCRIPT_DIR = Path(__file__).resolve().parents[4] / "scripts" / "ci"
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from impacted_corpus_test_suites import classify_suites  # noqa: E402


def test_classify_suites_maps_boundary_test_paths() -> None:
    changed = [
        "frontends/chat/tests/pact/chat-gateway.pact.test.ts",
        "apis/gateway/tests/contracts/test_gateway_corpus_projection_contract.py",
        "apis/gateway/tests/integration/test_corpus_dm_gateway_parity.py",
        "frontends/chat/tests/e2e/corpus-parity.spec.ts",
    ]
    suites = classify_suites(changed)
    assert suites == ["contract", "integration", "pact", "system"]


def test_classify_suites_returns_empty_for_unrelated_paths() -> None:
    suites = classify_suites(["docs/README.md"])
    assert suites == []
