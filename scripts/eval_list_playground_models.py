#!/usr/bin/env python3
r"""List models staged on the Modal playground LLM volume (eval-golden-sweep setup).

Uses ``LlmClient.list_models`` → ``GET /models/ollama`` (path alias; ADR-037). Prefer
``VECINITA_MODAL_LLM_PLAYGROUND_URL``; falls back to ``VECINITA_MODAL_LLM_URL``.

Examples:
--------
List available / pending tags::

  set -a && source prod.env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python scripts/eval_list_playground_models.py

JSON output for agents::

  uv run python scripts/eval_list_playground_models.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

from vecinita_eval.playground_setup import (
    PlaygroundSetupError,
    assert_no_legacy_ollama_url,
    format_model_listing,
    make_playground_client,
)
from vecinita_llm_client import LlmClientError
from vecinita_shared_schemas.playground_models import PlaygroundModelListResponse

if TYPE_CHECKING:
    from vecinita_shared_schemas.json_types import JsonObject


def main(argv: list[str] | None = None) -> int:
    """CLI entry: print playground model listing."""
    parser = argparse.ArgumentParser(
        description="List models on the Modal playground llm-models volume.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override playground/LLM Modal ASGI URL",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON {items:[{model_id, available}, ...]}",
    )
    parser.add_argument(
        "--available-only",
        action="store_true",
        help="Only print model_ids that are available=true",
    )
    args = parser.parse_args(argv)

    try:
        assert_no_legacy_ollama_url()
        client = make_playground_client(base_url=args.base_url)
    except PlaygroundSetupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except LlmClientError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        listing = client.list_models()
    except LlmClientError as exc:
        print(f"ERROR: list_models failed: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()

    items = listing.items
    if args.available_only:
        items = [item for item in items if item.available]

    if args.json:
        payload: JsonObject = {
            "items": [{"model_id": item.model_id, "available": item.available} for item in items]
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.available_only:
        for item in sorted(items, key=lambda row: row.model_id):
            print(item.model_id)
        return 0

    filtered = PlaygroundModelListResponse(items=list(items))
    text = format_model_listing(filtered)
    if text:
        print(text)
    else:
        print("(no models listed)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
