"""Smoke checks for local container runtime files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_exists_and_uses_asgi_entrypoint() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in dockerfile
    assert "vecinita.asgi:app" in dockerfile


def test_docker_compose_wires_api_to_ollama() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "ollama:" in compose
    assert "api:" in compose
    assert "OLLAMA_HOST: http://ollama:11434" in compose


def test_runtime_has_retry_window_guard_and_fail_fast_payload() -> None:
    app_source = (ROOT / "src/vecinita/app.py").read_text(encoding="utf-8")

    assert (
        "retry_window_ms = settings.retry_limit * settings.retry_backoff_ms"
        in app_source
    )
    assert "STARTUP_PRELOAD_FAILED" in app_source
    assert "recommended_operator_action" in app_source


def test_runtime_invokes_teardown_lifecycle_and_preserves_cache_strategy() -> None:
    app_source = (ROOT / "src/vecinita/app.py").read_text(encoding="utf-8")
    lifecycle_source = (ROOT / "src/vecinita/lifecycle.py").read_text(encoding="utf-8")

    assert "_run_teardown_lifecycle()" in app_source
    assert "default-teardown-cache-preserving" in lifecycle_source


def test_environment_specific_startup_model_selection_is_wired() -> None:
    config_source = (ROOT / "src/vecinita/config.py").read_text(encoding="utf-8")
    app_source = (ROOT / "src/vecinita/app.py").read_text(encoding="utf-8")

    assert "startup_model: str | None = None" in config_source
    assert 'lifecycle_registry_id: str = "default"' in config_source
    assert "resolve_startup_model_id()" in app_source


def test_transient_failure_retry_exhaustion_path_present() -> None:
    app_source = (ROOT / "src/vecinita/app.py").read_text(encoding="utf-8")

    assert "classify_connection_error(exc)" in app_source
    assert 'if failure_type == "permanent_failure":' in app_source
    assert "if attempt >= max_attempts:" in app_source
    assert "Startup preload failed after retry limit." in app_source


def test_storage_exhaustion_classified_as_permanent_failure_path() -> None:
    app_source = (ROOT / "src/vecinita/app.py").read_text(encoding="utf-8")

    assert "STARTUP_PRELOAD_PERMANENT_FAILURE" in app_source
    assert "Startup preload failed with permanent error." in app_source


def test_omitted_startup_model_configuration_falls_back_to_default() -> None:
    config_source = (ROOT / "src/vecinita/config.py").read_text(encoding="utf-8")

    assert (
        'model_id = (settings.startup_model or "").strip() or settings.default_model'
        in config_source
    )


def test_startup_to_ready_latency_measurement_artifacts_are_emitted() -> None:
    app_source = (ROOT / "src/vecinita/app.py").read_text(encoding="utf-8")

    assert (
        "retry_window_ms = settings.retry_limit * settings.retry_backoff_ms"
        in app_source
    )
    assert '"retry_window_ms": retry_window_ms' in app_source
    assert '"attempt_count": attempt' in app_source
