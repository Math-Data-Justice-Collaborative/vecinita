"""TC-311-01 companion: force-cold uses Modal CLI list+stop (EV-311)."""

from __future__ import annotations

import json

import pytest
from scripts.ops import cold_start_bench as bench

pytestmark = pytest.mark.unit

_LLM_APP = "vecinita-llm"
_ENV = "staging"
_CID_A = "ta-aaa"
_CID_B = "ta-bbb"
_CID_EMBED = "ta-embed"


class _FakeCompleted:
    """Minimal subprocess.CompletedProcess stand-in."""

    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_force_cold_lists_env_then_stops_matching_app_containers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Modal 1.5+: stop by container id after ``container list -e ENV --json``."""
    calls: list[list[str]] = []

    def fake_run(
        cmd: list[str],
        *,
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
    ) -> object:
        _ = (check, capture_output, text)
        calls.append(list(cmd))
        if cmd[:3] == ["modal", "container", "list"]:
            payload = [
                {
                    "container_id": _CID_A,
                    "app_name": _LLM_APP,
                },
                {
                    "container_id": _CID_B,
                    "app_name": _LLM_APP,
                },
                {
                    "container_id": _CID_EMBED,
                    "app_name": "vecinita-embedding",
                },
            ]
            return _FakeCompleted(0, json.dumps(payload), "")
        if cmd[:3] == ["modal", "container", "stop"]:
            return _FakeCompleted(0, "", "")
        return _FakeCompleted(1, "", "unexpected")

    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    bench.force_cold(app_name=_LLM_APP, environment=_ENV)

    assert calls[0] == [
        "modal",
        "container",
        "list",
        "-e",
        _ENV,
        "--json",
    ]
    stop_cmds = [c for c in calls if c[:3] == ["modal", "container", "stop"]]
    assert stop_cmds == [
        ["modal", "container", "stop", _CID_A, "-y"],
        ["modal", "container", "stop", _CID_B, "-y"],
    ]
    assert all(_CID_EMBED not in c for c in stop_cmds)


def test_force_cold_raises_when_list_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail closed if container list cannot run (do not silently warm-sample)."""

    def fake_run(
        cmd: list[str],
        *,
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
    ) -> object:
        _ = (cmd, check, capture_output, text)
        return _FakeCompleted(1, "", "boom")

    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="container list"):
        bench.force_cold(app_name=_LLM_APP, environment=_ENV)


def test_force_cold_ignores_already_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Treat ``already stopped`` as success (list/stop race)."""

    def fake_run(
        cmd: list[str],
        *,
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
    ) -> object:
        _ = (check, capture_output, text)
        if cmd[:3] == ["modal", "container", "list"]:
            payload = [{"container_id": _CID_A, "app_name": _LLM_APP}]
            return _FakeCompleted(0, json.dumps(payload), "")
        return _FakeCompleted(1, "", f"Container '{_CID_A}' is already stopped.")

    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    bench.force_cold(app_name=_LLM_APP, environment=_ENV)


def test_force_cold_raises_when_stop_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail closed if a matching container cannot be stopped for a real error."""

    def fake_run(
        cmd: list[str],
        *,
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
    ) -> object:
        _ = (check, capture_output, text)
        if cmd[:3] == ["modal", "container", "list"]:
            payload = [{"container_id": _CID_A, "app_name": _LLM_APP}]
            return _FakeCompleted(0, json.dumps(payload), "")
        return _FakeCompleted(1, "", "stop failed")

    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="container stop"):
        bench.force_cold(app_name=_LLM_APP, environment=_ENV)
