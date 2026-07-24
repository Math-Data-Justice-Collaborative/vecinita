#!/usr/bin/env python3
r"""Ensure playground model(s) are staged (and optionally warmed) for eval sweeps.

Uses ``LlmClient`` list/pull/warm against the Modal playground app (ADR-037). Prefer
``VECINITA_MODAL_LLM_PLAYGROUND_URL``. Path aliases ``/models/ollama*`` remain for FE
compat — this is HF Hub staging + vLLM warm, not ``ollama pull``.

Examples:
--------
Pull + wait + warm a model the agent chose::

  set -a && source prod.env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python scripts/eval_setup_playground_model.py --model qwen3:8b

Multiple models (comma-separated)::

  uv run python scripts/eval_setup_playground_model.py \
    --models qwen2.5:1.5b-instruct,qwen3:8b

Enqueue pull without waiting (no warm)::

  uv run python scripts/eval_setup_playground_model.py \
    --model mistral:7b --no-wait --no-warm
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

from vecinita_eval.playground_setup import (
    DEFAULT_POLL_INTERVAL_S,
    DEFAULT_PULL_TIMEOUT_S,
    PlaygroundSetupError,
    assert_no_legacy_ollama_url,
    ensure_model_ready,
    make_playground_client,
)
from vecinita_eval.sweep import parse_csv_strs
from vecinita_llm_client import LlmClientError

if TYPE_CHECKING:
    from vecinita_shared_schemas.json_types import JsonObject


def _parse_models(args: argparse.Namespace) -> list[str]:
    models = parse_csv_strs(args.models)
    if args.model.strip():
        models = [*models, args.model.strip()]
    # de-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for tag in models:
        if tag not in seen:
            seen.add(tag)
            ordered.append(tag)
    return ordered


def main(argv: list[str] | None = None) -> int:
    """CLI entry: pull (if needed) and warm specified playground models."""
    parser = argparse.ArgumentParser(
        description="Ensure playground LLM model(s) are available for golden eval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model",
        default="",
        help="Single model tag (repeatable via --models CSV)",
    )
    parser.add_argument(
        "--models",
        default="",
        help="Comma-separated model tags to stage",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override playground/LLM Modal ASGI URL",
    )
    parser.add_argument(
        "--no-pull",
        action="store_true",
        help="Fail if a model is not already available (do not enqueue pull)",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="After pull, do not poll until available (implies skip warm unless already ready)",
    )
    parser.add_argument(
        "--no-warm",
        action="store_true",
        help="Skip POST /warm after the model is available",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_S,
        help=f"Seconds between list polls while waiting (default {DEFAULT_POLL_INTERVAL_S})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_PULL_TIMEOUT_S,
        help=f"Max wait seconds after pull (default {DEFAULT_PULL_TIMEOUT_S})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON array of per-model results",
    )
    args = parser.parse_args(argv)

    models = _parse_models(args)
    if not models:
        print("ERROR: pass --model and/or --models", file=sys.stderr)
        return 1

    try:
        assert_no_legacy_ollama_url()
    except PlaygroundSetupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    results: list[JsonObject] = []
    for tag in models:
        try:
            client = make_playground_client(base_url=args.base_url, model_id=tag)
        except (PlaygroundSetupError, LlmClientError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        try:
            outcome = ensure_model_ready(
                client,
                tag,
                pull_if_missing=not args.no_pull,
                wait=not args.no_wait,
                warm=not args.no_warm,
                poll_interval_s=args.poll_interval,
                timeout_s=args.timeout,
            )
        except PlaygroundSetupError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        finally:
            client.close()

        row: JsonObject = {
            "model_id": outcome.model_id,
            "was_available": outcome.was_available,
            "pulled": outcome.pulled,
            "job_id": outcome.job_id,
            "warmed": outcome.warmed,
            "available": outcome.available,
        }
        results.append(row)
        if not args.json:
            status = "available" if outcome.available else "pending"
            actions: list[str] = []
            if outcome.pulled:
                actions.append("pulled")
            if outcome.warmed:
                actions.append("warmed")
            if not actions:
                actions.append("ready" if outcome.was_available else "listed")
            print(f"{outcome.model_id}\t{status}\t{','.join(actions)}")

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
