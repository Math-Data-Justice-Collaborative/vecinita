"""Cursor afterFileEdit hook: enforce the type-suppression policy (docs/typing-policy.md).

Ruff (`PGH003`) and basedpyright cannot express these project rules, so this hook catches
them on edit and reports via additional_context (advisory; always exits 0):

1. Blanket `# type: ignore` / `# pyright: ignore` without a bracketed code — never allowed.
2. `# type: ignore[code]` outside `tests/` — production/infra/scripts must use
   `# pyright: ignore[rule]` instead.

Comments are extracted with `tokenize`, so suppression strings inside string literals
(e.g. the codemod scripts that *generate* such comments) are not flagged.
"""

from __future__ import annotations

import json
import re
import sys
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_paths import find_repo_root, relative_parts

SOURCE_ROOTS = frozenset({"apps", "packages", "tests", "infra", "scripts"})

_BLANKET_TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore(?!\[)")
_CODED_TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore\[")
_BLANKET_PYRIGHT_IGNORE = re.compile(r"#\s*pyright:\s*ignore(?!\[)")


def _violations(path: Path, *, in_tests: bool) -> list[str]:
    messages: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            tokens = list(tokenize.generate_tokens(handle.readline))
    except (OSError, tokenize.TokenError, SyntaxError, IndentationError):
        return messages

    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        comment = token.string
        line = token.start[0]
        if _BLANKET_TYPE_IGNORE.search(comment):
            messages.append(
                f"{path}:{line} blanket `# type: ignore` is banned — add a specific code, "
                f"and in non-test code use `# pyright: ignore[rule]`."
            )
        elif _CODED_TYPE_IGNORE.search(comment) and not in_tests:
            messages.append(
                f"{path}:{line} `# type: ignore[...]` is only allowed under tests/ — "
                f"use `# pyright: ignore[rule]  # reason` here."
            )
        if _BLANKET_PYRIGHT_IGNORE.search(comment):
            messages.append(
                f"{path}:{line} `# pyright: ignore` must name a specific rule, e.g. "
                f"`# pyright: ignore[reportUnknownMemberType]  # reason`."
            )
    return messages


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    raw = payload.get("filePath") or payload.get("file_path") or ""
    if not raw:
        print("{}")
        return 0

    file_path = Path(raw)
    if file_path.suffix != ".py":
        print("{}")
        return 0

    repo = find_repo_root(file_path)
    if repo is None:
        print("{}")
        return 0

    parts = relative_parts(repo, file_path)
    if not parts or parts[0] not in SOURCE_ROOTS:
        print("{}")
        return 0

    messages = _violations(file_path.resolve(), in_tests=parts[0] == "tests")
    result = (
        {"additional_context": "[type-suppression] policy violations:\n" + "\n".join(messages)}
        if messages
        else {}
    )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
