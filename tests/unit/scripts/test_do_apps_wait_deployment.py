"""BUG-2026-09-09: DO deploy must wait for ACTIVE before returning (FE lag)."""

from __future__ import annotations

from typing import Any, cast

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


def test_wait_for_deployment_returns_when_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """Poll until ACTIVE; do not treat PENDING_BUILD as success."""
    sleeps: list[float] = []
    monkeypatch.setattr(do_apps.time, "sleep", lambda s: sleeps.append(float(s)))
    api = _FakeAppsApi(["PENDING_BUILD", "BUILDING", "ACTIVE"])
    client: Any = _FakeClient(api)
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
    monkeypatch.setattr(do_apps.time, "sleep", lambda _s: None)
    api = _FakeAppsApi(["ERROR"])
    client: Any = _FakeClient(api)
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
        def create_deployment(*, app_id: str, body: dict[str, object]) -> dict[str, object]:
            del app_id, body
            return {"deployment": {"id": "dep-9", "phase": "PENDING_BUILD"}}

    class _Client:
        apps = _Apps()

    monkeypatch.setattr(
        do_apps,
        "_iter_apps",
        lambda _c: [{"id": "app-9", "spec": {"name": "vecinita-staging-chat-fe"}}],
    )
    monkeypatch.setattr(
        do_apps,
        "_find_app",
        lambda _apps, name: {"id": "app-9", "spec": {"name": name}},
    )

    def _wait(
        _c: object,
        *,
        app_id: str,
        deployment_id: str,
        timeout_s: float,
    ) -> str:
        waited.append(f"{app_id}:{deployment_id}:{timeout_s}")
        return "ACTIVE"

    monkeypatch.setattr(do_apps, "wait_for_deployment", _wait)
    rc = do_apps.cmd_deploy(cast("Any", _Client()), "vecinita-staging-chat-fe", wait=True)
    assert rc == 0
    assert waited == ["app-9:dep-9:900"]
