#!/usr/bin/env python3
r"""Opt-in cold-start latency harness (EV-314 / #314 + EV-320 / F85).

Modes:

* ``generate`` (default) — Modal ``POST /generate`` with GPU ``cold_kind`` tags.
* ``chat-ask`` — ChatRAG ``POST /api/v1/ask`` with ``answer_path`` tags
  (``faq_bypass`` vs ``rag_llm``). Never stamps FAQ as a GPU ``cold_kind`` (AC-320-05).

Synthetic / fixture prompts only — never pass user chat (ADR-004).

Examples::

    uv run python scripts/ops/cold_start_bench.py --n 20 --output /tmp/cold-smoke.json
    uv run python scripts/ops/cold_start_bench.py --n 100 --force-cold --output /tmp/cold-p95.json
    uv run python scripts/ops/cold_start_bench.py --mode chat-ask --chat-url "$VECINITA_STAGING_CHAT_URL" \
        --faq-question "What is Vecinita?" --n 20 --output /tmp/faq-bypass.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import httpx
from vecinita_shared_schemas.cold_start_latency import (
    summarize_by_answer_path,
    summarize_latencies,
    validate_answer_path_latency_sample,
    validate_cold_start_sample,
)

_SYNTHETIC_PROMPT: Final[str] = "Context: pantry hours are 9am. Question: when is the pantry open?"
_DEFAULT_FAQ_QUESTION: Final[str] = "What is Vecinita?"
_DEFAULT_APP: Final[str] = "vecinita-llm"
_DEFAULT_ENV: Final[str] = "staging"
_PUBLISH_N: Final[int] = 100


def _proxy_headers(proxy_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Vecinita-Proxy-Key": proxy_key,
    }


def _post_generate(
    url: str,
    body: dict[str, object],
    *,
    headers: dict[str, str],
    timeout_s: float,
) -> None:
    response = httpx.post(url, json=body, headers=headers, timeout=timeout_s)
    _ = response.raise_for_status()


def _post_chat_ask(
    ask_url: str,
    *,
    question: str,
    timeout_s: float,
) -> dict[str, object]:
    response = httpx.post(
        ask_url,
        json={"question": question},
        headers={"Content-Type": "application/json"},
        timeout=timeout_s,
    )
    _ = response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        msg = "ask response must be a JSON object"
        raise TypeError(msg)
    return payload


def _force_cold(*, app_name: str, environment: str) -> None:
    """Documented staging procedure: stop running containers so the next call restores cold."""
    cmd = [
        "modal",
        "container",
        "stop",
        "--env",
        environment,
        "--all",
        app_name,
    ]
    print(f"+ {' '.join(cmd)}", file=sys.stderr)
    _ = subprocess.run(cmd, check=False)


def _one_generate_sample(
    *,
    generate_url: str,
    proxy_key: str,
    cold_kind: str,
    timeout_s: float,
) -> dict[str, object]:
    t0 = time.perf_counter()
    _post_generate(
        generate_url,
        {"prompt": _SYNTHETIC_PROMPT, "max_tokens": 8, "temperature": 0.0},
        headers=_proxy_headers(proxy_key),
        timeout_s=timeout_s,
    )
    first_token_ms = (time.perf_counter() - t0) * 1000.0
    sample = validate_cold_start_sample(
        {
            "cold_kind": cold_kind,
            "event": "first_token",
            "first_token_ms": first_token_ms,
        }
    )
    return dict(sample)


def _one_chat_ask_sample(
    *,
    ask_url: str,
    question: str,
    timeout_s: float,
) -> dict[str, object]:
    t0 = time.perf_counter()
    payload = _post_chat_ask(ask_url, question=question, timeout_s=timeout_s)
    first_token_ms = (time.perf_counter() - t0) * 1000.0
    path_raw = payload.get("answer_path", "rag_llm")
    if not isinstance(path_raw, str):
        path_raw = "rag_llm"
    sample = validate_answer_path_latency_sample(
        {
            "answer_path": path_raw,
            "event": "chat_ask",
            "first_token_ms": first_token_ms,
        }
    )
    return dict(sample)


def main(argv: list[str] | None = None) -> int:
    """CLI entry — Layer E smoke / publish harness."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--mode",
        choices=["generate", "chat-ask"],
        default="generate",
        help="generate=Modal /generate + cold_kind; chat-ask=ChatRAG ask + answer_path",
    )
    _ = parser.add_argument(
        "--n", type=int, default=20, help="Samples (default 20 smoke; 100 publish)"
    )
    _ = parser.add_argument(
        "--llm-url",
        default=os.environ.get("VECINITA_MODAL_LLM_URL", ""),
        help="Modal LLM base URL (or VECINITA_MODAL_LLM_URL)",
    )
    _ = parser.add_argument(
        "--proxy-key",
        default=os.environ.get("VECINITA_MODAL_PROXY_KEY", ""),
        help="Proxy key (or VECINITA_MODAL_PROXY_KEY)",
    )
    _ = parser.add_argument(
        "--chat-url",
        default=os.environ.get("VECINITA_STAGING_CHAT_URL", ""),
        help="ChatRAG base URL for --mode chat-ask (or VECINITA_STAGING_CHAT_URL)",
    )
    _ = parser.add_argument(
        "--faq-question",
        default=_DEFAULT_FAQ_QUESTION,
        help="Reviewed FAQ fixture variant for chat-ask (never log this into samples)",
    )
    _ = parser.add_argument("--timeout-s", type=float, default=180.0)
    _ = parser.add_argument(
        "--cold-kind",
        default="snapshot_restore",
        choices=["warm", "snapshot_restore", "snapshot_create", "clean_boot"],
    )
    _ = parser.add_argument(
        "--force-cold",
        action="store_true",
        help="Run `modal container stop --all` before sampling (staging; generate mode)",
    )
    _ = parser.add_argument("--modal-app", default=_DEFAULT_APP)
    _ = parser.add_argument(
        "--modal-env", default=os.environ.get("MODAL_ENVIRONMENT", _DEFAULT_ENV)
    )
    _ = parser.add_argument("--output", type=Path, required=True, help="JSON report path")
    args = parser.parse_args(argv)

    if args.n < 1:
        print("--n must be >= 1", file=sys.stderr)
        return 2

    if args.mode == "chat-ask":
        return _run_chat_ask(args)
    return _run_generate(args)


def _run_generate(args: argparse.Namespace) -> int:
    if not args.llm_url or not args.proxy_key:
        print("Need --llm-url and --proxy-key (or env)", file=sys.stderr)
        return 2

    if args.force_cold:
        _force_cold(app_name=args.modal_app, environment=args.modal_env)

    generate_url = f"{args.llm_url.rstrip('/')}/generate"
    samples: list[dict[str, object]] = []
    latencies: list[float] = []
    for index in range(args.n):
        if args.force_cold and index > 0:
            _force_cold(app_name=args.modal_app, environment=args.modal_env)
        try:
            sample = _one_generate_sample(
                generate_url=generate_url,
                proxy_key=args.proxy_key,
                cold_kind=args.cold_kind,
                timeout_s=args.timeout_s,
            )
        except (httpx.HTTPError, TimeoutError, OSError) as exc:
            print(f"sample {index + 1}/{args.n} failed: {exc}", file=sys.stderr)
            return 1
        samples.append(sample)
        ft = sample.get("first_token_ms")
        if isinstance(ft, (int, float)):
            latencies.append(float(ft))
        print(f"sample {index + 1}/{args.n}: first_token_ms={ft}", file=sys.stderr)

    summary = summarize_latencies(latencies)
    report: dict[str, object] = {
        "mode": "generate",
        "n": args.n,
        "cold_kind": args.cold_kind,
        "publishable_p95": args.n >= _PUBLISH_N,
        "note": (
            "Statistical p95 requires n>=100 (AC-314-03). "
            "Do not conflate with prewarm_to_ready (#318)."
        ),
        "summary": summary,
        "samples": samples,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0


def _run_chat_ask(args: argparse.Namespace) -> int:
    if not args.chat_url:
        print("Need --chat-url (or VECINITA_STAGING_CHAT_URL) for --mode chat-ask", file=sys.stderr)
        return 2

    ask_url = f"{args.chat_url.rstrip('/')}/api/v1/ask"
    samples: list[dict[str, object]] = []
    for index in range(args.n):
        try:
            sample = _one_chat_ask_sample(
                ask_url=ask_url,
                question=args.faq_question,
                timeout_s=args.timeout_s,
            )
        except (httpx.HTTPError, TimeoutError, OSError, TypeError, ValueError) as exc:
            print(f"sample {index + 1}/{args.n} failed: {exc}", file=sys.stderr)
            return 1
        samples.append(sample)
        ft = sample.get("first_token_ms")
        path = sample.get("answer_path")
        print(
            f"sample {index + 1}/{args.n}: answer_path={path} first_token_ms={ft}",
            file=sys.stderr,
        )

    path_summary = summarize_by_answer_path(samples)
    report: dict[str, object] = {
        "mode": "chat-ask",
        "n": args.n,
        "publishable_p95": args.n >= _PUBLISH_N,
        "note": (
            "FAQ path uses answer_path (faq_bypass|rag_llm); never cold_kind "
            "(AC-320-05 / ADR-022 EV-320). Question text is not written to samples."
        ),
        "answer_path_summary": path_summary,
        "samples": samples,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(path_summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
