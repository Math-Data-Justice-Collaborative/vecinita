"""Unit tests for runtime backend and importable infrastructure modules."""

from __future__ import annotations

import importlib
import subprocess
from abc import ABC
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from vecinita.api.schemas import Message
from vecinita.lifecycle import LifecyclePlugin, PluginRegistry
from vecinita.models.base import BaseModelBackend
from vecinita.models.ollama import OllamaBackend, classify_connection_error


class TestInfrastructureModules:
    def test_imports_modal_infrastructure_modules(self):
        images = importlib.import_module("vecinita.images")
        volumes = importlib.import_module("vecinita.volumes")
        asgi = importlib.import_module("vecinita.asgi")

        assert images.ollama_image is not None
        assert volumes.models_volume is not None
        assert volumes.MODELS_PATH == "/models"
        assert asgi.app is not None


class TestBaseModelBackend:
    def test_is_abstract(self):
        assert issubclass(BaseModelBackend, ABC)

        with pytest.raises(TypeError):
            BaseModelBackend()

    def test_concrete_subclass_implements_contract(self):
        class FakeBackend(BaseModelBackend):
            def chat(self, messages, **kwargs):
                return messages[-1].content

            def stream(self, messages, **kwargs):
                yield messages[-1].content

            def is_healthy(self):
                return True

        backend = FakeBackend()
        messages = [Message(role="user", content="hola")]

        assert backend.chat(messages) == "hola"
        assert list(backend.stream(messages)) == ["hola"]
        assert backend.is_healthy() is True


class TestOllamaBackend:
    def test_chat_returns_response_content(self):
        backend = OllamaBackend("llama3.2")
        backend._client = MagicMock()
        backend._client.chat.return_value = SimpleNamespace(
            message=SimpleNamespace(content="hello")
        )
        messages = [Message(role="user", content="hi")]

        result = backend.chat(messages, temperature=0.2, max_tokens=12)

        assert result == "hello"
        backend._client.chat.assert_called_once_with(
            model="llama3.2",
            messages=[{"role": "user", "content": "hi"}],
            options={"temperature": 0.2, "num_predict": 12},
        )

    def test_stream_yields_chunk_content(self):
        backend = OllamaBackend("mistral")
        backend._client = MagicMock()
        backend._client.chat.return_value = iter(
            [
                SimpleNamespace(message=SimpleNamespace(content="foo")),
                SimpleNamespace(message=SimpleNamespace(content="bar")),
            ]
        )
        messages = [Message(role="user", content="stream")]

        result = list(backend.stream(messages, max_tokens=5))

        assert result == ["foo", "bar"]
        backend._client.chat.assert_called_once_with(
            model="mistral",
            messages=[{"role": "user", "content": "stream"}],
            stream=True,
            options={"num_predict": 5},
        )

    def test_is_healthy_returns_true_when_list_succeeds(self):
        backend = OllamaBackend("phi3")
        backend._client = MagicMock()

        assert backend.is_healthy() is True

    def test_is_healthy_returns_false_when_list_fails(self):
        backend = OllamaBackend("phi3")
        backend._client = MagicMock()
        backend._client.list.side_effect = RuntimeError("down")

        assert backend.is_healthy() is False

    def test_build_options_filters_none_values(self):
        backend = OllamaBackend("phi3")

        assert backend._build_options({}) == {}
        assert backend._build_options({"temperature": 0.3}) == {"temperature": 0.3}
        assert backend._build_options({"max_tokens": 10}) == {"num_predict": 10}
        assert backend._build_options({"temperature": None, "max_tokens": None}) == {}

    def test_start_server_waits_until_client_is_ready(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        client_factory = MagicMock()
        client_factory.return_value.list.side_effect = [RuntimeError("booting"), None]
        sleep = MagicMock()

        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setattr("time.sleep", sleep)
        monkeypatch.setattr("ollama.Client", client_factory)

        result = OllamaBackend.start_server(models_path="/tmp/models")

        assert result is proc
        subprocess.Popen.assert_called_once()
        sleep.assert_called_once_with(0.5)

    def test_start_server_raises_when_timeout_expires(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        client_factory = MagicMock()
        client_factory.return_value.list.side_effect = RuntimeError("still booting")

        class FakeTime:
            def __init__(self):
                self.now = 100.0

            def time(self):
                self.now += 31.0
                return self.now

        fake_time = FakeTime()

        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setattr("time.time", fake_time.time)
        monkeypatch.setattr("time.sleep", MagicMock())
        monkeypatch.setattr("ollama.Client", client_factory)

        with pytest.raises(RuntimeError, match="did not start"):
            OllamaBackend.start_server()

    def test_start_server_timeout_handles_terminate_failure(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        proc.terminate.side_effect = RuntimeError("cannot terminate")
        client_factory = MagicMock()
        client_factory.return_value.list.side_effect = RuntimeError("still booting")

        class FakeTime:
            def __init__(self):
                self.now = 100.0

            def time(self):
                self.now += 31.0
                return self.now

        fake_time = FakeTime()
        warning = MagicMock()

        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setattr("time.time", fake_time.time)
        monkeypatch.setattr("time.sleep", MagicMock())
        monkeypatch.setattr("ollama.Client", client_factory)
        monkeypatch.setattr("vecinita.models.ollama.logger.warning", warning)

        with pytest.raises(RuntimeError, match="did not start"):
            OllamaBackend.start_server()

        warning.assert_called_once()

    def test_start_server_timeout_handles_kill_failure(self, monkeypatch):
        proc = MagicMock(spec=subprocess.Popen)
        proc.wait.side_effect = subprocess.TimeoutExpired(cmd="ollama", timeout=5)
        proc.kill.side_effect = RuntimeError("cannot kill")
        client_factory = MagicMock()
        client_factory.return_value.list.side_effect = RuntimeError("still booting")

        class FakeTime:
            def __init__(self):
                self.now = 100.0

            def time(self):
                self.now += 31.0
                return self.now

        fake_time = FakeTime()
        warning = MagicMock()

        monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=proc))
        monkeypatch.setattr("time.time", fake_time.time)
        monkeypatch.setattr("time.sleep", MagicMock())
        monkeypatch.setattr("ollama.Client", client_factory)
        monkeypatch.setattr("vecinita.models.ollama.logger.warning", warning)

        with pytest.raises(RuntimeError, match="did not start"):
            OllamaBackend.start_server()

        proc.terminate.assert_called_once_with()
        proc.wait.assert_called_once_with(timeout=5)
        proc.kill.assert_called_once_with()
        warning.assert_called_once()


class TestConnectionFailureClassification:
    def test_classifies_transient_connection_errors(self):
        err = RuntimeError("Connection refused while contacting ollama")
        assert classify_connection_error(err) == "transient_failure"

    def test_classifies_non_transient_errors_as_permanent(self):
        err = RuntimeError("unsupported model identifier")
        assert classify_connection_error(err) == "permanent_failure"


class TestStartupModelResolution:
    def test_raises_for_unsupported_startup_model(self, monkeypatch):
        from vecinita import config as config_module

        monkeypatch.setattr(config_module.settings, "startup_model", "bad-model")
        with pytest.raises(ValueError, match="Unsupported startup model"):
            config_module.resolve_startup_model_id()

    def test_settings_rejects_non_positive_retry_limit(self):
        from vecinita.config import Settings

        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            Settings(retry_limit=0)


class TestTeardownOrdering:
    def test_registry_executes_teardown_plugins_in_deterministic_order(self):
        registry = PluginRegistry("ordered")
        order: list[str] = []

        registry.register(
            LifecyclePlugin(
                plugin_id="teardown-b",
                phase="teardown",
                order=20,
                hook=lambda _ctx: order.append("b"),
            )
        )
        registry.register(
            LifecyclePlugin(
                plugin_id="teardown-a",
                phase="teardown",
                order=10,
                hook=lambda _ctx: order.append("a"),
            )
        )

        registry.execute_phase("teardown", {"correlation_id": "cid-order"})
        assert order == ["a", "b"]