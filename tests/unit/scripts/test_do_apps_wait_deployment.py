"""BUG-2026-09-09: DO deploy must wait for ACTIVE before returning (FE lag)."""

from __future__ import annotations

from typing import cast

import pytest
from deploy import do_apps

pytestmark = pytest.mark.unit


class _FakeAppsApi:
    def __init__(self, phases: list[str]) -> None:
        self._phases = list(phases)
        self.gets = 0

    def get_deployment(self, *, app_id: str, deployment_id: str) -> dict[str, object]:
        del app_id, deployment_id
        phase = self._phases[min(self.gets, len(self._phases) - 1)]
        self.gets += 1
        return {"deployment": {"id": "dep-1", "phase": phase}}


class _FakeClient:
    def __init__(self, api: _FakeAppsApi) -> None:
        self.apps = api


def _noop_sleep(_seconds: float) -> None:
    return None


def test_wait_for_deployment_returns_when_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """Poll until ACTIVE; do not treat PENDING_BUILD as success."""
    sleeps: list[float] = []

    def _record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(do_apps.time, "sleep", _record_sleep)
    api = _FakeAppsApi(["PENDING_BUILD", "BUILDING", "ACTIVE"])
    client = _FakeClient(api)
    phase = do_apps.wait_for_deployment(
        client,
        app_id="app-1",
        deployment_id="dep-1",
        timeout_s=30,
        poll_s=0.01,
    )
    assert phase == "ACTIVE"
    assert api.gets >= len(["PENDING_BUILD", "BUILDING", "ACTIVE"])
    assert sleeps


def test_wait_for_deployment_raises_on_error_phase(monkeypatch: pytest.MonkeyPatch) -> None:
    """ERROR / CANCELED phases fail closed."""
    monkeypatch.setattr(do_apps.time, "sleep", _noop_sleep)
    api = _FakeAppsApi(["ERROR"])
    client = _FakeClient(api)
    with pytest.raises(SystemExit, match="ERROR"):
        _ = do_apps.wait_for_deployment(
            client,
            app_id="app-1",
            deployment_id="dep-1",
            timeout_s=5,
            poll_s=0.01,
        )


def test_cmd_deploy_wait_flag_calls_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """cmd_deploy(--wait) polls until ACTIVE."""
    waited: list[str] = []

    class _Apps:
        @staticmethod
        def create_deployment(
            *,
            app_id: str,
            body: dict[str, object],
        ) -> dict[str, object]:
            del app_id, body
            return {"deployment": {"id": "dep-9", "phase": "PENDING_BUILD"}}

    class _Client:
        apps = _Apps()

    def _iter_apps(_client: object) -> list[dict[str, object]]:
        return [{"id": "app-9", "spec": {"name": "vecinita-staging-chat-fe"}}]

    def _find_app(
        _apps: list[dict[str, object]],
        name: str,
    ) -> dict[str, object]:
        return {"id": "app-9", "spec": {"name": name}}

    def _wait(
        _client: object,
        *,
        app_id: str,
        deployment_id: str,
        timeout_s: float,
    ) -> str:
        waited.append(f"{app_id}:{deployment_id}:{timeout_s}")
        return "ACTIVE"

    monkeypatch.setattr(do_apps, "_iter_apps", _iter_apps)
    monkeypatch.setattr(do_apps, "_find_app", _find_app)
    monkeypatch.setattr(do_apps, "wait_for_deployment", _wait)
    rc = do_apps.cmd_deploy(cast("object", _Client()), "vecinita-staging-chat-fe", wait=True)
    assert rc == 0
    assert waited == ["app-9:dep-9:900"]
