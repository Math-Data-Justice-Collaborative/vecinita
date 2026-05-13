"""Unit tests for Modal app helpers and setup code."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from vecinita import app as app_module
from vecinita.lifecycle import LifecyclePlugin, PluginRegistry, make_lifecycle_event
from vecinita.volumes import MODELS_PATH


class TestOllamaEnv:
    def test_sets_models_path_without_mutating_process_env(self):
        original = os.environ.get("OLLAMA_MODELS")
        env = app_module._ollama_env()

        assert env["OLLAMA_MODELS"] == MODELS_PATH
        assert os.environ.get("OLLAMA_MODELS") == original


class TestDeploymentDefaults:
    def test_default_model_is_gemma3(self):
        config_source = Path(__file__).resolve().parents[1] / "src/vecinita/config.py"
        content = config_source.read_text(encoding="utf-8")
        assert 'default_model: str = "gemma3"' in content

    def test_chat_completion_uses_cpu_only(self):
        # Assert on Modal's resolved spec (not a raw source substring) so refactors
        # and quote style cannot false-fail CI while the deployment stays CPU-only.
        gpus = app_module.chat_completion.spec.gpus
        assert not gpus, (
            f"chat_completion should not request a GPU (CPU inference), got {gpus!r}"
        )
        cpu = app_module.chat_completion.spec.cpu
        assert cpu is not None and cpu >= 4.0, (
            f"chat_completion should allocate CPU cores, got {cpu!r}"
        )


class TestDownloadModel:
    def test_rejects_unknown_model(self):
        raw_download_model = app_module.download_model.get_raw_f()

        with pytest.raises(ValueError, match="Unknown model 'bad-model'"):
            raw_download_model("bad-model")

    def test_pulls_model_and_commits_volume(self, monkeypatch):
        raw_download_model = app_module.download_model.get_raw_f()
        proc = MagicMock(spec=subprocess.Popen)
        client = MagicMock()
        client.list.return_value = SimpleNamespace(models=[])
        ollama_module = SimpleNamespace(
            Client=MagicMock(return_value=client),
            pull=MagicMock(),
        )
        sleep = MagicMock()
        commit = MagicMock()

        monkeypatch.setattr(app_module, "models_volume", SimpleNamespace(commit=commit))
        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setattr("time.sleep", sleep)
        monkeypatch.setitem(__import__("sys").modules, "ollama", ollama_module)

        raw_download_model("llama3.2")

        subprocess.Popen.assert_called_once()
        client.pull.assert_called_once_with("llama3.2")
        commit.assert_called_once_with()
        proc.terminate.assert_called_once_with()
        sleep.assert_not_called()

    def test_download_default_model_function_exists_in_source(self):
        app_source_path = Path(__file__).resolve().parents[1] / "src/vecinita/app.py"
        app_source = app_source_path.read_text(encoding="utf-8")
        assert "def download_default_model()" in app_source
        assert "resolved = resolve_startup_model_id()" in app_source
        assert "_download_model_if_missing(resolved)" in app_source

    def test_download_helper_skips_pull_when_already_present(self):
        app_source_path = Path(__file__).resolve().parents[1] / "src/vecinita/app.py"
        app_source = app_source_path.read_text(encoding="utf-8")
        assert "if ollama_name in installed:" in app_source
        assert "skipping pull" in app_source

    def test_terminates_server_when_pull_fails(self, monkeypatch):
        raw_download_model = app_module.download_model.get_raw_f()
        proc = MagicMock(spec=subprocess.Popen)
        client = MagicMock()
        client.list.return_value = SimpleNamespace(models=[])
        client.pull.side_effect = RuntimeError("pull failed")
        ollama_module = SimpleNamespace(
            Client=MagicMock(return_value=client),
            pull=MagicMock(),
        )

        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setitem(__import__("sys").modules, "ollama", ollama_module)

        with pytest.raises(RuntimeError, match="pull failed"):
            raw_download_model("llama3.2")

        proc.terminate.assert_called_once_with()

    def test_raises_clear_error_when_server_never_ready(self, monkeypatch):
        raw_download_model = app_module.download_model.get_raw_f()
        proc = MagicMock(spec=subprocess.Popen)
        client = MagicMock()
        client.list.side_effect = RuntimeError("still starting")
        ollama_module = SimpleNamespace(
            Client=MagicMock(return_value=client),
            pull=MagicMock(),
        )

        class FakeTime:
            def __init__(self):
                self.now = 0.0

            def time(self):
                self.now += 31.0
                return self.now

        fake_time = FakeTime()

        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setattr("time.time", fake_time.time)
        monkeypatch.setattr("time.sleep", MagicMock())
        monkeypatch.setitem(__import__("sys").modules, "ollama", ollama_module)

        with pytest.raises(RuntimeError, match="did not become ready"):
            raw_download_model("llama3.2")

        client.pull.assert_not_called()
        proc.terminate.assert_called_once_with()


class TestLifecycleRuntime:
    def test_startup_lifecycle_retries_then_succeeds(self, monkeypatch):
        pull = MagicMock(side_effect=[RuntimeError("connection refused"), None])
        events: list[dict] = []
        sleep = MagicMock()

        monkeypatch.setattr(app_module.settings, "startup_model", None)
        monkeypatch.setattr(app_module.settings, "default_model", "gemma3")
        monkeypatch.setattr(app_module, "_download_model_if_missing", pull)
        monkeypatch.setattr(app_module, "_emit_lifecycle_event", events.append)
        monkeypatch.setattr("time.sleep", sleep)
        monkeypatch.setattr(app_module.settings, "retry_limit", 2)
        monkeypatch.setattr(app_module.settings, "retry_backoff_ms", 10)

        app_module._run_startup_lifecycle()

        assert pull.call_count == 2
        assert any(event["event_type"] == "retry" for event in events)
        assert events[-1]["event_type"] == "preload_success"

    def test_startup_lifecycle_fail_fast_has_required_error_fields(self, monkeypatch):
        monkeypatch.setattr(app_module.settings, "startup_model", None)
        monkeypatch.setattr(app_module.settings, "default_model", "gemma3")
        monkeypatch.setattr(
            app_module,
            "_download_model_if_missing",
            MagicMock(side_effect=RuntimeError("connection refused")),
        )
        monkeypatch.setattr(app_module.settings, "retry_limit", 2)
        monkeypatch.setattr(app_module.settings, "retry_backoff_ms", 1)
        emitted: list[dict] = []
        monkeypatch.setattr(app_module, "_emit_lifecycle_event", emitted.append)
        monkeypatch.setattr("time.sleep", MagicMock())

        with pytest.raises(RuntimeError, match="Startup preload failed"):
            app_module._run_startup_lifecycle()

        failures = [
            event for event in emitted if event["event_type"] == "preload_failure"
        ]
        failure = failures[0]
        details = failure["details"]
        assert details["error_code"] == "STARTUP_PRELOAD_FAILED"
        assert details["failure_phase"] == "startup"
        assert details["attempt_count"] == 2
        assert "recommended_operator_action" in details

    def test_teardown_lifecycle_emits_non_silent_failure(self, monkeypatch):
        def boom(_context: dict[str, object]) -> None:
            raise RuntimeError("cleanup denied")

        monkeypatch.setattr(
            app_module,
            "_teardown_cache_preserving_hook",
            boom,
        )
        emitted: list[dict] = []
        monkeypatch.setattr(app_module, "_emit_lifecycle_event", emitted.append)

        with pytest.raises(RuntimeError, match="cleanup denied"):
            app_module._run_teardown_lifecycle(correlation_id="cid-1")

        assert any(event["event_type"] == "teardown_failure" for event in emitted)

    def test_startup_lifecycle_permanent_error_fails_immediately(self, monkeypatch):
        monkeypatch.setattr(app_module.settings, "startup_model", None)
        monkeypatch.setattr(app_module.settings, "default_model", "gemma3")
        monkeypatch.setattr(
            app_module,
            "_download_model_if_missing",
            MagicMock(side_effect=RuntimeError("unsupported model id")),
        )
        monkeypatch.setattr(app_module.settings, "retry_limit", 4)
        emitted: list[dict] = []
        monkeypatch.setattr(app_module, "_emit_lifecycle_event", emitted.append)

        with pytest.raises(RuntimeError, match="permanent error"):
            app_module._run_startup_lifecycle()

        retries = [event for event in emitted if event["event_type"] == "retry"]
        assert retries == []

    def test_teardown_lifecycle_success_event_emitted(self, monkeypatch):
        emitted: list[dict] = []
        monkeypatch.setattr(app_module, "_emit_lifecycle_event", emitted.append)
        app_module._run_teardown_lifecycle(correlation_id="cid-ok")
        teardown_success = [
            event for event in emitted if event["event_type"] == "teardown_success"
        ]
        assert len(teardown_success) == 1
        assert teardown_success[0]["details"] == {
            "cache_preserved": True,
            "temp_artifacts_cleaned": True,
        }

    def test_startup_lifecycle_rejects_non_positive_retry_limit(self, monkeypatch):
        monkeypatch.setattr(app_module.settings, "startup_model", None)
        monkeypatch.setattr(app_module.settings, "default_model", "gemma3")
        monkeypatch.setattr(app_module.settings, "retry_limit", 0)

        with pytest.raises(ValueError, match="retry_limit must be >= 1"):
            app_module._run_startup_lifecycle()


class TestDownloadModelIfMissing:
    def test_skips_pull_when_model_already_installed(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        model_name = "gemma3"
        ollama_name = app_module.SUPPORTED_MODELS[model_name]["ollama_name"]
        client = MagicMock()
        client.list.return_value = SimpleNamespace(
            models=[SimpleNamespace(model=ollama_name)]
        )
        ollama_module = SimpleNamespace(
            Client=MagicMock(return_value=client),
            pull=MagicMock(),
        )
        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setitem(__import__("sys").modules, "ollama", ollama_module)

        app_module._download_model_if_missing(model_name)

        client.pull.assert_not_called()
        proc.terminate.assert_called_once_with()


class TestChatCompletionImplementation:
    def test_chat_completion_impl_returns_chat_payload(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        chat_payload = {"message": {"content": "hello"}}
        client = MagicMock()
        client.chat.return_value = chat_payload
        ollama_module = SimpleNamespace(Client=MagicMock(return_value=client))
        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setitem(__import__("sys").modules, "ollama", ollama_module)
        monkeypatch.setattr(
            app_module,
            "_wait_for_ollama_ready",
            lambda timeout_seconds=30: None,
        )
        monkeypatch.setattr(
            app_module,
            "_ensure_startup_model_downloaded",
            lambda: None,
        )
        monkeypatch.setattr(app_module, "_run_teardown_lifecycle", lambda: None)

        result = app_module._chat_completion_impl(
            model="gemma3",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.1,
        )

        assert result == chat_payload
        proc.terminate.assert_called_once_with()
        client.chat.assert_called_once()
        call_kw = client.chat.call_args.kwargs
        assert call_kw["model"] == "gemma3"

    def test_chat_completion_empty_model_defaults_to_gemma3(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        chat_payload = {"message": {"content": "hello"}}
        client = MagicMock()
        client.chat.return_value = chat_payload
        ollama_module = SimpleNamespace(Client=MagicMock(return_value=client))
        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setitem(__import__("sys").modules, "ollama", ollama_module)
        monkeypatch.setattr(
            app_module,
            "_wait_for_ollama_ready",
            lambda timeout_seconds=30: None,
        )
        monkeypatch.setattr(
            app_module,
            "_ensure_startup_model_downloaded",
            lambda: None,
        )
        monkeypatch.setattr(app_module, "_run_teardown_lifecycle", lambda: None)
        monkeypatch.setattr(app_module.settings, "default_model", "gemma3")

        app_module._chat_completion_impl(
            model="",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.0,
        )

        call_kw = client.chat.call_args.kwargs
        assert call_kw["model"] == "gemma3"

    def test_chat_completion_unknown_model_resolves_to_default(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        chat_payload = {"message": {"content": "hello"}}
        client = MagicMock()
        client.chat.return_value = chat_payload
        ollama_module = SimpleNamespace(Client=MagicMock(return_value=client))
        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setitem(__import__("sys").modules, "ollama", ollama_module)
        monkeypatch.setattr(
            app_module,
            "_wait_for_ollama_ready",
            lambda timeout_seconds=30: None,
        )
        monkeypatch.setattr(
            app_module,
            "_ensure_startup_model_downloaded",
            lambda: None,
        )
        monkeypatch.setattr(app_module, "_run_teardown_lifecycle", lambda: None)
        monkeypatch.setattr(app_module.settings, "default_model", "gemma3")

        app_module._chat_completion_impl(
            model="totally-unknown-id",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.0,
        )

        call_kw = client.chat.call_args.kwargs
        assert call_kw["model"] == "gemma3"


class TestLifecycleFoundations:
    def test_plugin_registry_validates_duplicate_order(self):
        registry = PluginRegistry("test")
        registry.register(
            LifecyclePlugin(
                plugin_id="a",
                phase="startup",
                order=1,
                hook=lambda _ctx: None,
            )
        )
        with pytest.raises(ValueError, match="Duplicate plugin order"):
            registry.register(
                LifecyclePlugin(
                    plugin_id="b",
                    phase="startup",
                    order=1,
                    hook=lambda _ctx: None,
                )
            )

    def test_lifecycle_event_has_required_schema_fields(self):
        event = make_lifecycle_event(
            event_type="preload_start",
            phase="startup",
            correlation_id="cid-2",
            details={"x": 1},
        )
        assert set(["event_type", "phase", "correlation_id", "timestamp"]).issubset(
            event.keys()
        )

    def test_resolve_ollama_model_name_passthrough_and_alias(self):
        assert app_module._resolve_ollama_model_name("gemma3") == "gemma3"
        assert app_module._resolve_ollama_model_name("mistral") == "mistral"
        assert app_module._resolve_ollama_model_name("custom:latest") == "gemma3"

    def test_resolve_unknown_model_falls_back_to_default(self, monkeypatch):
        monkeypatch.setattr(app_module.settings, "default_model", "phi3")
        assert app_module._resolve_ollama_model_name("not-a-real-model") == "phi3"

    def test_ensure_default_model_downloaded_aliases_startup_helper(self, monkeypatch):
        called = {"count": 0}

        def _fake() -> None:
            called["count"] += 1

        monkeypatch.setattr(app_module, "_ensure_startup_model_downloaded", _fake)
        app_module._ensure_default_model_downloaded()
        assert called["count"] == 1
