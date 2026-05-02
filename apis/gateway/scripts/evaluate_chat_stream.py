#!/usr/bin/env python3
"""Quick stream/non-stream chat evaluation for gateway reliability.

Usage:
  python backend/scripts/evaluate_chat_stream.py \
    --base-url http://localhost:8004/api/v1 \
    --question "Testing 1 2 3"
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class StreamEvalResult:
    ok: bool
    event_count: int
    first_event_ms: int | None
    complete_received: bool
    assistant_answer_len: int
    error_message: str | None


def evaluate_stream(base_url: str, question: str, timeout: int) -> StreamEvalResult:
    stream_url = f"{base_url.rstrip('/')}/ask/stream"
    started = time.perf_counter()
    first_event_ms: int | None = None
    event_count = 0
    complete_received = False
    assistant_answer_len = 0
    error_message: str | None = None

    with requests.get(
        stream_url,
        params={"question": question},
        stream=True,
        timeout=timeout,
        headers={"Accept": "text/event-stream"},
    ) as response:
        response.raise_for_status()

        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            if not raw_line.startswith("data:"):
                continue

            payload = raw_line[5:].strip()
            if not payload:
                continue

            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue

            event_count += 1
            if first_event_ms is None:
                first_event_ms = int((time.perf_counter() - started) * 1000)

            event_type = event.get("type")
            if event_type == "error":
                error_message = event.get("message") or "unknown stream error"
                break

            if event_type == "complete":
                complete_received = True
                assistant_answer_len = len((event.get("answer") or "").strip())
                break

    ok = complete_received and assistant_answer_len > 0 and not error_message
    return StreamEvalResult(
        ok=ok,
        event_count=event_count,
        first_event_ms=first_event_ms,
        complete_received=complete_received,
        assistant_answer_len=assistant_answer_len,
        error_message=error_message,
    )


def evaluate_non_stream(base_url: str, question: str, timeout: int) -> tuple[bool, int, str | None]:
    ask_url = f"{base_url.rstrip('/')}/ask"
    response = requests.get(
        ask_url,
        params={"question": question},
        timeout=timeout,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()

    body: dict[str, Any] = response.json()
    answer = (body.get("answer") or "").strip()
    if answer:
        return True, len(answer), None

    return False, 0, "empty non-stream answer"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate /ask/stream and /ask reliability")
    parser.add_argument("--base-url", default="http://localhost:8004/api/v1")
    parser.add_argument("--question", default="Testing 1 2 3")
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()

    print(f"Evaluating gateway at: {args.base_url}")
    print(f"Question: {args.question}")

    stream_result = evaluate_stream(args.base_url, args.question, args.timeout)
    print("\n[stream]")
    print(f"  ok={stream_result.ok}")
    print(f"  event_count={stream_result.event_count}")
    print(f"  first_event_ms={stream_result.first_event_ms}")
    print(f"  complete_received={stream_result.complete_received}")
    print(f"  assistant_answer_len={stream_result.assistant_answer_len}")
    print(f"  error={stream_result.error_message}")

    non_stream_ok = False
    non_stream_len = 0
    non_stream_error: str | None = None
    try:
        non_stream_ok, non_stream_len, non_stream_error = evaluate_non_stream(
            args.base_url, args.question, args.timeout
        )
    except Exception as exc:  # pragma: no cover - diagnostics script
        non_stream_error = str(exc)

    print("\n[non-stream]")
    print(f"  ok={non_stream_ok}")
    print(f"  answer_len={non_stream_len}")
    print(f"  error={non_stream_error}")

    if stream_result.ok or non_stream_ok:
        print("\nPASS: At least one response path produced a non-empty answer.")
        return 0

    print("\nFAIL: Both stream and non-stream paths failed to produce a non-empty answer.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
