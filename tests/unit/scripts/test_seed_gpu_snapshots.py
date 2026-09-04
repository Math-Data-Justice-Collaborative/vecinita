"""TC-315: seed GPU snapshots with fail-closed cold_kind evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
from scripts.ops import seed_gpu_snapshots

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit

_BAD_INPUT_EXIT = 2
_LIVE_PRIME_COUNT = 2


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


def test_parse_cold_kinds_from_log_text_extracts_stamp_kinds() -> None:
    """EV-315: parse Modal/app log lines for cold_start_stamp cold_kind values."""
    log_text = """
    Restoring Function from memory snapshot.
    cold_start_stamp {'cold_kind': 'snapshot_restore', 'event': 'adapter_ready'}
    cold_start_stamp {"cold_kind": "warm", "event": "first_token"}
    unrelated line
    cold_kind=snapshot_create
    Creating memory snapshot for Function.
    """
    kinds = seed_gpu_snapshots.parse_cold_kinds_from_log_text(log_text)
    assert kinds == [
        "snapshot_restore",
        "snapshot_restore",
        "warm",
        "snapshot_create",
        "snapshot_create",
    ]


def test_read_kinds_file_ignores_non_kind_log_noise(tmp_path: Path) -> None:
    """Raw Modal logs without stamps must not invent unknown kinds via CSV split."""
    path = tmp_path / "noise.log"
    noise = (
        "2026-09-04 INFO starting worker, gpu=T4, region=us\n"
        "Restoring Function from memory snapshot.\n"
    )
    _ = path.write_text(noise, encoding="utf-8")
    kinds = seed_gpu_snapshots.read_kinds_file(path)
    assert kinds == ["snapshot_restore"]
    assert seed_gpu_snapshots.evaluate_seed_outcome(kinds) == 0


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


def test_main_live_path_fails_closed_without_observed_kinds(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live /warm alone must not claim restore without observed cold_kind (AC-315-01)."""
    calls: list[str] = []

    def fake_post(
        url: str,
        *,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        _ = (json, headers, timeout)
        calls.append(url)
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
            str(_LIVE_PRIME_COUNT),
        ],
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert len(calls) == _LIVE_PRIME_COUNT
    assert "no restore evidence" in captured.err.lower()


def test_main_live_path_posts_authenticated_warm_with_explicit_assume_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live mode primes authenticated /warm; explicit --assume-kind is opt-in only."""
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


def test_main_kinds_file_parses_log_stamps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--kinds-file accepts raw log text and extracts cold_kind evidence."""

    def fail_post(*args: object, **kwargs: object) -> httpx.Response:
        _ = (args, kwargs)
        msg = "network must not be called when --kinds-file is set"
        raise AssertionError(msg)

    monkeypatch.setattr(httpx, "post", fail_post)
    kinds_path = tmp_path / "modal-logs.txt"
    _ = kinds_path.write_text(
        "cold_start_stamp {'cold_kind': 'snapshot_restore', 'event': 'adapter_ready'}\n",
        encoding="utf-8",
    )
    exit_code = seed_gpu_snapshots.main(["--kinds-file", str(kinds_path)])
    assert exit_code == 0


def test_main_requires_live_url_and_proxy_key_without_observations(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live mode fails as bad input without authenticated Modal endpoint details."""
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)
    monkeypatch.delenv("VECINITA_STAGING_MODAL_LLM_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
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
