#!/usr/bin/env python3
r"""Create or append golden eval examples (eval-golden-set.md schema).

Pipeline step: example generation.

Examples:
--------
Append one case from CLI flags::

  uv run python scripts/eval_create_golden_examples.py \
    --id community-new-wifi-hours \
    --locale en \
    --domain community \
    --question "What are the library Wi-Fi hours?" \
    --expected-doc-url fixture://corpus/en/community-resources.md \
    --retrieval-expectation hit \
    --required-fact "The library offers free Wi-Fi" \
    --fixture data/fixtures/eval/qa_pairs.json \
    --append

Import a draft JSON array/object::

  uv run python scripts/eval_create_golden_examples.py \
    --draft data/fixtures/eval/draft_examples.json \
    --fixture data/fixtures/eval/qa_pairs.json \
    --append
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from vecinita_eval.golden_draft import (
    append_golden_rows,
    build_golden_row,
    golden_row_to_json,
    parse_golden_draft,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_FIXTURE = _REPO_ROOT / "data" / "fixtures" / "eval" / "qa_pairs.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create or append golden eval examples.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--draft", type=Path, default=None, help="JSON draft file (object or array)"
    )
    parser.add_argument("--id", default="", help="Case id (CLI single-row mode)")
    parser.add_argument("--locale", default="", help="en or es")
    parser.add_argument("--domain", default="", help="community, housing, legal, or edge")
    parser.add_argument("--question", default="", help="User question text")
    parser.add_argument("--expected-doc-url", default=None, help="Single expected URL (hit)")
    parser.add_argument(
        "--expected-doc-url-multi",
        action="append",
        default=[],
        help="Repeatable expected URL (any_of)",
    )
    parser.add_argument(
        "--retrieval-expectation",
        default="hit",
        choices=["hit", "any_of", "abstain", "empty"],
    )
    parser.add_argument(
        "--required-fact",
        action="append",
        default=[],
        help="Repeatable required fact bullet",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=_DEFAULT_FIXTURE,
        help="Target qa_pairs.json path",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Write into --fixture (otherwise print JSON only)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing same id+locale rows when appending",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write the new rows JSON only",
    )
    args = parser.parse_args(argv)

    try:
        if args.draft is not None:
            loaded = cast("object", json.loads(args.draft.read_text(encoding="utf-8")))
            rows = parse_golden_draft(loaded)
        else:
            rows = [
                build_golden_row(
                    case_id=args.id,
                    locale=args.locale,
                    domain=args.domain,
                    question=args.question,
                    retrieval_expectation=args.retrieval_expectation,
                    required_facts=args.required_fact,
                    expected_doc_url=args.expected_doc_url,
                    expected_doc_urls=args.expected_doc_url_multi,
                )
            ]
    except (TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = [golden_row_to_json(row) for row in rows]
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {args.out}", file=sys.stderr)

    if args.append:
        try:
            merged = append_golden_rows(
                fixture_path=args.fixture,
                new_rows=rows,
                replace_same_id_locale=args.replace,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"Appended to {args.fixture} (total rows={len(merged)})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
