#!/usr/bin/env python3
"""
SC-005 benchmark: twenty representative ``GET /api/v1/ask`` calls per **calendar day** (UTC),
tracked across **three consecutive** days.

Run **once per day** (for example via cron). Appends today's counts to a JSON state file. After
the history contains **three consecutive** UTC days ending today, exits **1** if any of those
days had fewer than ``--min-per-day`` successes (default **18**).

Environment (optional; flags override)::

    GATEWAY_BASE_URL   Gateway origin (e.g. https://vecinita-gateway.onrender.com)
    GATEWAY_BEARER_TOKEN   Bearer when gateway auth is enabled

Usage (from repo root)::

    python backend/scripts/benchmark_ask_three_day.py \\
        --base-url https://<gateway-host> \\
        --token \"$GATEWAY_BEARER_TOKEN\"

    python backend/scripts/benchmark_ask_three_day.py --base-url https://<host> --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

DEFAULT_QUESTIONS: tuple[str, ...] = (
    "Where can I apply for rental assistance?",
    "What documents do I need for WIC?",
    "How do I dispute a utility shutoff notice?",
    "Are cooling centers open this weekend?",
    "What are the income limits for SNAP in my county?",
    "¿Dónde puedo renovar mi pase de autobús reducido?",
    "How do I report unsafe housing conditions?",
    "What is the school enrollment deadline?",
    "Where is the nearest food bank?",
    "How do I appeal a Section 8 denial?",
    "¿Qué servicios ofrece la clínica comunitaria?",
    "What are walk-in hours at the housing intake office?",
    "How do I request a reasonable accommodation?",
    "Where can I find tenant rights workshops?",
    "What is the process for a pay-or-quit notice?",
    "¿Cómo solicito asistencia legal gratuita?",
    "How do I update my address for benefits?",
    "What transit discounts exist for seniors?",
    "Where can I get help filling out immigration forms?",
    "How do I file a noise complaint with the city?",
)


@dataclass
class DayResult:
    date: str
    successes: int
    attempts: int


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _last_three_consecutive_days(history: list[DayResult]) -> list[DayResult] | None:
    """Last three days of the consecutive UTC streak ending at the most recent history entry."""
    if len(history) < 3:
        return None
    streak: list[DayResult] = [history[-1]]
    for i in range(len(history) - 2, -1, -1):
        cur_d = date.fromisoformat(history[i].date)
        expected = date.fromisoformat(streak[0].date) - timedelta(days=1)
        if cur_d == expected:
            streak.insert(0, history[i])
        else:
            break
    if len(streak) < 3:
        return None
    return streak[-3:]


def _run_day(
    client: httpx.Client,
    base: str,
    token: str,
    questions: tuple[str, ...],
    request_timeout: float,
) -> tuple[int, int]:
    successes = 0
    base_headers: dict[str, str] = {}
    if token.strip():
        base_headers["Authorization"] = f"Bearer {token.strip()}"
    for q in questions:
        headers = dict(base_headers)
        headers["X-Correlation-ID"] = str(uuid.uuid4())
        try:
            r = client.get(
                f"{base.rstrip('/')}/api/v1/ask",
                params={"question": q},
                headers=headers,
                timeout=request_timeout,
            )
        except httpx.HTTPError:
            continue
        if 200 <= r.status_code < 300:
            successes += 1
    return successes, len(questions)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--base-url",
        default=os.environ.get(
            "GATEWAY_BASE_URL", os.environ.get("SCHEMA_SMOKE_GATEWAY_URL", "")
        ).strip(),
    )
    p.add_argument("--token", default=os.environ.get("GATEWAY_BEARER_TOKEN", "").strip())
    p.add_argument(
        "--state-file",
        type=Path,
        default=Path(os.environ.get("ASK_BENCHMARK_STATE_FILE", ".benchmark-ask-sc005.json")),
    )
    p.add_argument("--min-per-day", type=int, default=18)
    p.add_argument(
        "--request-timeout",
        type=float,
        default=float(os.environ.get("ASK_BENCHMARK_HTTP_TIMEOUT", "180")),
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    if not args.base_url:
        print(
            "error: --base-url or GATEWAY_BASE_URL / SCHEMA_SMOKE_GATEWAY_URL is required",
            file=sys.stderr,
        )
        return 2

    questions = DEFAULT_QUESTIONS
    today = _utc_today()

    with httpx.Client() as client:
        successes, attempts = _run_day(
            client,
            args.base_url,
            args.token,
            questions,
            args.request_timeout,
        )

    if args.dry_run:
        print(f"dry-run: successes={successes}/{attempts} (UTC {today})")
        return 0

    history: list[DayResult] = []
    if args.state_file.exists():
        try:
            blob = json.loads(args.state_file.read_text(encoding="utf-8"))
            for row in blob.get("history", []):
                if isinstance(row, dict) and "date" in row:
                    history.append(
                        DayResult(
                            date=str(row["date"]),
                            successes=int(row.get("successes", 0)),
                            attempts=int(row.get("attempts", 0)),
                        )
                    )
        except (OSError, json.JSONDecodeError):
            history = []

    if history and history[-1].date == today:
        history[-1] = DayResult(date=today, successes=successes, attempts=attempts)
    else:
        history.append(DayResult(date=today, successes=successes, attempts=attempts))

    args.state_file.write_text(
        json.dumps({"history": [asdict(d) for d in history]}, indent=2) + "\n",
        encoding="utf-8",
    )

    window = _last_three_consecutive_days(history)
    print(f"UTC {today}: successes={successes}/{attempts}; history_days={len(history)}")
    if window is None:
        print(
            "SC-005: need three consecutive UTC days ending today in history; "
            "run again on following days (see quickstart §5)."
        )
        return 0

    mins = min(d.successes for d in window)
    if mins < args.min_per_day:
        print(
            f"SC-005 FAIL: one of the last three consecutive days had successes < {args.min_per_day} "
            f"(min={mins}). Record a waiver in baseline-notes-schemathesis.md if intentional.",
            file=sys.stderr,
        )
        return 1
    print("SC-005 PASS: last three consecutive UTC days met the per-day success threshold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
