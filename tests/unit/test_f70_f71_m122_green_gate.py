"""T122.1 - Phase 28 green gate: TC-232-241 unit + stubbed API e2e mapped.

Compose-backed UJ-076 e2e remains waived this cycle (S027-D35). No Playwright (S027-D16).

[Corpus: feature-list.md §F70]
[Corpus: feature-list.md §F71]
[Spec: docs/test-plan.md §TC-232-241]
[Spec: docs/acceptance-criteria.md §AC-ME1-ME11]
[Spec: docs/decisions/evolve-decisions.md §S027-D16 / S027-D35 / S027-D40]
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_TEST_PLAN = _REPO / "docs" / "test-plan.md"
_ACCEPTANCE = _REPO / "docs" / "acceptance-criteria.md"
_DECISIONS = _REPO / "docs" / "decisions" / "evolve-decisions.md"

# TC → primary unit/stub-e2e modules (paths relative to repo root).
_TC_COVERAGE: dict[str, tuple[str, ...]] = {
    "TC-232": (
        "tests/e2e/test_uj076_embed_promote_report.py",
        "tests/unit/shared_schemas/test_f71_rebuild_tokenizer_stamps.py",
    ),
    "TC-233": ("tests/unit/test_embedding_prefixes_runtime.py",),
    "TC-234": (
        "tests/unit/test_embedding_prefixes_runtime.py",
        "tests/unit/test_embedding_modal_pins.py",
    ),
    "TC-235": (
        "tests/unit/shared_schemas/test_f71_embed_promote_report.py",
        "tests/unit/internal_write_api/test_f71_embed_promote_report.py",
    ),
    "TC-236": (
        "tests/unit/shared_schemas/test_f71_embed_promote_report.py",
        "tests/unit/internal_write_api/test_f71_embed_promote_report.py",
    ),
    "TC-237": ("tests/e2e/test_uj075_multilingual_ask.py",),
    "TC-238": ("tests/e2e/test_uj075_multilingual_ask.py",),
    "TC-239": (
        "tests/unit/shared_schemas/test_f71_e0_rollback.py",
        "tests/unit/internal_write_api/test_f71_e0_rollback.py",
        "tests/e2e/test_uj076_embed_promote_report.py",
    ),
    "TC-240": (
        "tests/unit/test_f71_tc240_cutover_runbook.py",
        "tests/unit/test_f71_m121_green_gate.py",
    ),
    "TC-241": (
        "tests/unit/shared_schemas/test_f71_rebuild_tokenizer_stamps.py",
        "tests/e2e/test_uj075_multilingual_ask.py",
    ),
}

_AC_ME_IDS = tuple(f"AC-ME{n}" for n in range(1, 12))


@pytest.mark.unit
def test_tc232_241_mapped_in_test_plan() -> None:
    """T122.1: every TC-232-241 section exists in docs/test-plan.md."""
    plan = _TEST_PLAN.read_text(encoding="utf-8")
    for tc in _TC_COVERAGE:
        assert f"### {tc}:" in plan, f"missing {tc} in test-plan"


@pytest.mark.unit
def test_ac_me1_11_mapped_in_acceptance_criteria() -> None:
    """T122.1: AC-ME1-ME11 present for Phase 28 gate."""
    text = _ACCEPTANCE.read_text(encoding="utf-8")
    for ac in _AC_ME_IDS:
        assert f"**{ac}**" in text, f"missing {ac}"


@pytest.mark.unit
def test_tc232_241_coverage_modules_exist() -> None:
    """T122.1: unit + API e2e modules for TC-232-241 are on disk."""
    missing: list[str] = []
    for tc, rels in _TC_COVERAGE.items():
        for rel in rels:
            path = _REPO / rel
            if not path.is_file():
                missing.append(f"{tc} → {rel}")
    assert missing == [], f"missing coverage modules: {missing}"


@pytest.mark.unit
def test_no_playwright_for_multilingual_journeys_d16() -> None:
    """T122.1 / S027-D16: UJ-075/076 stay API e2e - no new Playwright specs."""
    plan = _TEST_PLAN.read_text(encoding="utf-8")
    # Journey map rows for UJ-075/076 must not claim Playwright UI coverage.
    assert "UJ-075" in plan
    assert "UJ-076" in plan
    assert "(no UI)" in plan or "- (no UI)" in plan
    playwright_specs = list((_REPO / "apps").rglob("*multilingual*.spec.*"))
    playwright_specs += list((_REPO / "apps").rglob("*uj075*.spec.*"))
    playwright_specs += list((_REPO / "apps").rglob("*uj076*.spec.*"))
    assert playwright_specs == [], f"unexpected Playwright specs: {playwright_specs}"


@pytest.mark.unit
def test_compose_e2e_waiver_s027_d35_still_recorded() -> None:
    """T122.1: compose-backed UJ-076 remains waived (S027-D35); unit gate stands."""
    decisions = _DECISIONS.read_text(encoding="utf-8")
    assert "S027-D35" in decisions
    assert "Waive" in decisions or "waive" in decisions.lower()
    assert "compose" in decisions.lower()
