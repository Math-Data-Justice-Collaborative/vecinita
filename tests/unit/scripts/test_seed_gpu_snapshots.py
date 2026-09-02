"""TC-315: seed GPU snapshots with fail-closed cold_kind evaluation."""

from __future__ import annotations

import httpx
import pytest
from scripts.ops import seed_gpu_snapshots

pytestmark = pytest.mark.unit

_BAD_INPUT_EXIT = 2


def test_evaluate_seed_outcome_succeeds_when_restore_observed() -> None:
    """EV-315 / ADR-022: at least one snapshot_restore makes seeding successful."""
    exit_code = seed_gpu_snapshots.evaluate_seed_outcome(
        ["snapshot_create", "snapshot_restore"],
    )
    assert exit_code == 0


def test_evaluate_seed_outcome_fails_closed_when_create_persists() -> None:
    """EV-315 / ADR-022: create-only observations never pass the seed gate."""
    exit_code = seed_gpu_snapshots.evaluate_seed_outcome(
        ["snapshot_create", "snapshot_create"],
    )
    assert exit_code == 1


def test_evaluate_seed_outcome_fails_closed_for_empty_observations() -> None:
    """EV-315 / ADR-022: no observations means no restore evidence."""
    exit_code = seed_gpu_snapshots.evaluate_seed_outcome([])
    assert exit_code == 1


def test_evaluate_seed_outcome_rejects_unknown_kind() -> None:
    """EV-315 / ADR-022: unknown cold_kind values are bad input."""
    exit_code = seed_gpu_snapshots.evaluate_seed_outcome(["snapshot_restore", "mystery"])
    assert exit_code == _BAD_INPUT_EXIT


def test_main_observed_kinds_does_not_call_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dry simulation evaluates supplied kinds only, with no live Modal calls."""

    def fail_post(*args: object, **kwargs: object) -> httpx.Response:
        _ = (args, kwargs)
        msg = "network must not be called when --observed-kinds is set"
        raise AssertionError(msg)

    monkeypatch.setattr(httpx, "post", fail_post)

    exit_code = seed_gpu_snapshots.main(
        [
            "--observed-kinds",
            "snapshot_create,snapshot_restore",
            "--modal-env",
            "staging",
        ],
    )
    assert exit_code == 0


def test_main_live_path_posts_authenticated_warm_without_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live mode primes authenticated /warm with an empty synthetic body."""
    calls: list[tuple[str, dict[str, object], dict[str, str], float]] = []

    def fake_post(
        url: str,
        *,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        calls.append((url, json, headers, timeout))
        return httpx.Response(
            200,
            json={"status": "warming"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    exit_code = seed_gpu_snapshots.main(
        [
            "--llm-url",
            "https://vecinita-staging--vecinita-llm-fastapi-app.modal.run/",
            "--proxy-key",
            "test-proxy-key",
            "--max-primes",
            "2",
            "--assume-kind",
            "snapshot_restore",
        ],
    )
    assert exit_code == 0
    assert calls == [
        (
            "https://vecinita-staging--vecinita-llm-fastapi-app.modal.run/warm",
            {},
            {
                "Content-Type": "application/json",
                "X-Vecinita-Proxy-Key": "test-proxy-key",
            },
            180.0,
        ),
        (
            "https://vecinita-staging--vecinita-llm-fastapi-app.modal.run/warm",
            {},
            {
                "Content-Type": "application/json",
                "X-Vecinita-Proxy-Key": "test-proxy-key",
            },
            180.0,
        ),
    ]


def test_main_requires_live_url_and_proxy_key_without_observations(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live mode fails as bad input without authenticated Modal endpoint details."""
    exit_code = seed_gpu_snapshots.main(["--max-primes", "1"])
    captured = capsys.readouterr()
    assert exit_code == _BAD_INPUT_EXIT
    assert "Need --llm-url and --proxy-key" in captured.err


def test_main_rejects_zero_max_primes(capsys: pytest.CaptureFixture[str]) -> None:
    """EV-315 / ADR-022: a zero-prime live run cannot seed or observe restore."""
    exit_code = seed_gpu_snapshots.main(
        [
            "--llm-url",
            "https://vecinita-staging--vecinita-llm-fastapi-app.modal.run",
            "--proxy-key",
            "test-proxy-key",
            "--max-primes",
            "0",
        ],
    )
    captured = capsys.readouterr()
    assert exit_code == _BAD_INPUT_EXIT
    assert "--max-primes must be >= 1" in captured.err
