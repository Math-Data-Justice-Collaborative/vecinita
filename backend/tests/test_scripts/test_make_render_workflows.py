"""Regression checks for root Makefile Render workflow shortcuts."""

from pathlib import Path

MAKEFILE_PATH = Path(__file__).resolve().parents[3] / "Makefile"


def _content() -> str:
    return MAKEFILE_PATH.read_text(encoding="utf-8")


def test_makefile_exists() -> None:
    assert MAKEFILE_PATH.exists(), "Expected root Makefile to exist"


def test_render_targets_declared_in_phony() -> None:
    content = _content()
    assert "render-env-validate" in content
    assert "render-tests-strict" in content
    assert "render-tests-render-suite" in content
    assert "render-workflow-ci" in content
    assert "render-local-validate" in content
    assert "render-local-check" in content
    assert "render-local-check-live" in content


def test_render_env_validate_target_runs_validator_script() -> None:
    content = _content()
    assert "render-env-validate:" in content
    assert "python3 scripts/github/validate_render_env.py" in content


def test_render_and_strict_targets_run_expected_test_files() -> None:
    content = _content()
    assert "render-tests-render-suite:" in content
    assert "tests/integration/test_service_integration_points_contract.py" in content
    assert "tests/integration/test_service_integration_points_contract_expanded.py" in content

    assert "render-tests-strict:" in content
    assert "No strict-mode routing suite remains; skipping." in content


def test_render_workflow_ci_chains_validation_and_suite() -> None:
    content = _content()
    assert "render-workflow-ci: render-env-validate render-tests-render-suite" in content


def test_render_local_check_has_preflight_and_live_mode_split() -> None:
    content = _content()
    assert "render-local-validate:" in content
    assert "docker compose -f docker-compose.render-local.yml config >/dev/null" in content

    assert "render-local-check:" in content
    assert "[render-local-check] Preflight validation (env + compose config)" in content
    assert "make render-local-up" in content
    assert "make render-local-check-live" in content

    assert "render-local-check-live:" in content
    assert "./scripts/local-render-check.sh --skip-simulation" in content
