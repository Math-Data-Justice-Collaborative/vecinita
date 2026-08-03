#!/usr/bin/env python3
"""Strict semver helpers for post-CD release tagging (F63 / #103 / S025-D11)."""

from __future__ import annotations

import argparse
import re
import sys

_STRICT_TAG = re.compile(r"^v([0-9]+)\.([0-9]+)\.([0-9]+)$")
_SKIP_MARKER = "[skip release]"


def strict_semver_tags(tags: list[str]) -> list[str]:
    """Return tags matching vMAJOR.MINOR.PATCH, sorted ascending."""
    matched: list[tuple[int, int, int, str]] = []
    for tag in tags:
        m = _STRICT_TAG.fullmatch(tag.strip())
        if m is None:
            continue
        matched.append((int(m.group(1)), int(m.group(2)), int(m.group(3)), tag.strip()))
    matched.sort()
    return [t[-1] for t in matched]


def next_patch_tag(tags: list[str]) -> str:
    """Compute next patch tag from latest strict semver; bootstrap v0.1.0 if none."""
    strict = strict_semver_tags(tags)
    if not strict:
        return "v0.1.0"
    m = _STRICT_TAG.fullmatch(strict[-1])
    if m is None:  # pragma: no cover — guarded by strict_semver_tags
        return "v0.1.0"
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"v{major}.{minor}.{patch + 1}"


def should_skip_release(
    commit_message: str,
    *,
    head_tags: list[str] | None = None,
) -> bool:
    """True when [skip release] is present or HEAD already has a strict tag."""
    if _SKIP_MARKER in commit_message:
        return True
    if head_tags is None:
        return False
    return bool(strict_semver_tags(head_tags))


def main(argv: list[str] | None = None) -> int:
    """CLI: print next tag or 'skip' for GitHub Actions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tags",
        nargs="*",
        default=[],
        help="Existing git tags (space-separated)",
    )
    parser.add_argument(
        "--commit-message",
        default="",
        help="HEAD commit message",
    )
    parser.add_argument(
        "--head-tags",
        nargs="*",
        default=[],
        help="Tags already pointing at HEAD",
    )
    args = parser.parse_args(argv)
    if should_skip_release(args.commit_message, head_tags=list(args.head_tags)):
        print("skip")
        return 0
    print(next_patch_tag(list(args.tags)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
