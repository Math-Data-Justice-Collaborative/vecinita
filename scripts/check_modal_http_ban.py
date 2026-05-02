#!/usr/bin/env python3
"""
Static check for HTTP(S) usage targeting Modal deployment hosts (FR-001 / SC-005).

1. Loads literal host fragments from config/modal_http_ban_patterns.txt.
2. Optional path allowlist (config/modal_http_ban_allowlist_paths.txt) suppresses **URL-only**
   matches in legacy OpenAPI/docs strings until US3 removes them.
3. Flags a line when:
   - it contains an https?:// URL whose host matches a blocked fragment, outside allowlist URL
     suppression rules, OR
   - it contains both a blocked fragment and an HTTP client call token (httpx./requests./…)
     on the same line.

Intentional gaps (extend before claiming full FR-001 coverage):
- No dataflow / multi-line URL construction analysis.
- Does not scan *.md.
- Test trees under **/tests/**, **/*.test.ts(x)**, **/*.spec.ts(x)**, and **/e2e/** are skipped.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PATTERNS_FILE = REPO_ROOT / "config" / "modal_http_ban_patterns.txt"
ALLOWLIST_FILE = REPO_ROOT / "config" / "modal_http_ban_allowlist_paths.txt"

DEFAULT_ROOTS = (
    "backend",
    "services",
    "frontends",
    "apps",
    "packages",
    "scripts",
)

RG_GLOBS = (
    "*.py",
    "*.ts",
    "*.tsx",
    "*.js",
    "*.jsx",
    "*.mts",
    "*.cts",
)

RG_NEGATED_GLOBS = (
    "!**/node_modules/**",
    "!**/.venv/**",
    "!**/venv/**",
    "!**/dist/**",
    "!**/build/**",
    "!**/__pycache__/**",
    "!**/.git/**",
    "!**/coverage/**",
    "!**/packages/openapi-clients/**",
    "!**/backend/tests/**",
    "!**/services/**/tests/**",
    "!**/frontends/**/tests/**",
    "!**/apps/**/tests/**",
    "!**/*.test.ts",
    "!**/*.test.tsx",
    "!**/*.spec.ts",
    "!**/*.spec.tsx",
    "!**/tests/e2e/**",
    "!**/backend/tests/fixtures/modal_http_ban/**",
)

URL_MODAL = re.compile(r"https?://[^\s\"'`<>]+", re.IGNORECASE)
CLIENT_RE = re.compile(
    r"(httpx\.(get|post|put|patch|delete|head|options|request|stream)|"
    r"httpx\.AsyncClient|httpx\.Client|"
    r"requests\.(get|post|put|patch|delete|head|options|request|Session)|"
    r"urllib\.(request\.urlopen|urlretrieve)|"
    r"axios\.(get|post|put|patch|delete|request)|"
    r"\bfetch\s*\()",
    re.IGNORECASE,
)


def _load_patterns() -> list[str]:
    if not PATTERNS_FILE.is_file():
        print(f"check_modal_http_ban: missing {PATTERNS_FILE}", file=sys.stderr)
        sys.exit(2)
    out: list[str] = []
    for line in PATTERNS_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    if not out:
        print("check_modal_http_ban: no patterns in config file", file=sys.stderr)
        sys.exit(2)
    return out


def _load_allowlist() -> set[str]:
    if not ALLOWLIST_FILE.is_file():
        return set()
    out: set[str] = set()
    for line in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip().replace("\\", "/")
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return out


def _is_allowlisted(rel_posix: str, allow: set[str]) -> bool:
    return any(
        rel_posix == p or rel_posix.startswith(p + "/") for p in allow
    )


def _url_targets_modal(line: str, patterns: list[str]) -> bool:
    for m in URL_MODAL.finditer(line):
        frag = m.group(0).lower()
        if any(p.lower() in frag for p in patterns):
            return True
    return False


def _line_violates(rel_posix: str, line: str, patterns: list[str], allow: set[str]) -> bool:
    lower = line.lower()
    if not any(p.lower() in lower for p in patterns):
        return False
    has_url_modal = _url_targets_modal(line, patterns)
    has_client = bool(CLIENT_RE.search(line))
    allowlisted = _is_allowlisted(rel_posix, allow)

    if allowlisted:
        # Still flag real client calls toward Modal on the same line.
        return bool(has_client and (has_url_modal or any(p.lower() in lower for p in patterns)))

    return bool(has_url_modal or has_client)


def _rg_available() -> bool:
    return shutil.which("rg") is not None


def _collect_hits_rg(patterns: list[str], roots: list[Path]) -> list[tuple[str, str]]:
    """Return list of (relative_posix_path, line_content) for lines containing any pattern."""
    hits: list[tuple[str, str]] = []
    for pat in patterns:
        args = [
            "rg",
            "-F",
            "--color",
            "never",
            "--no-heading",
            "-n",
            pat,
        ]
        for g in RG_GLOBS:
            args.extend(["--glob", g])
        for g in RG_NEGATED_GLOBS:
            args.extend(["--glob", g])
        for r in roots:
            if r.is_dir():
                args.append(str(r))
        proc = subprocess.run(
            args,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        if proc.returncode not in (0, 1):
            print(proc.stderr, file=sys.stderr)
            sys.exit(proc.returncode or 2)
        for raw in proc.stdout.splitlines():
            if not raw:
                continue
            # path:line:content — content may contain colons
            head, sep, tail = raw.partition(":")
            if not sep:
                continue
            mid, sep2, content = tail.partition(":")
            if not sep2 or not mid.isdigit():
                continue
            rel = Path(head).resolve().relative_to(REPO_ROOT).as_posix()
            hits.append((rel, content))
    return hits


def _collect_hits_fallback(patterns: list[str], roots: list[Path]) -> list[tuple[str, str]]:
    exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"}
    skip_name_substrings = (
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "__pycache__",
        ".git",
        "coverage",
        "openapi-clients",
    )
    hits: list[tuple[str, str]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in exts:
                continue
            if any(s in path.parts for s in skip_name_substrings):
                continue
            rel = path.resolve().relative_to(REPO_ROOT).as_posix()
            if "/tests/" in rel or rel.endswith(".test.ts") or rel.endswith(".spec.ts"):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                if any(p in line for p in patterns):
                    hits.append((rel, line))
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional roots to scan (relative to repo). Default: application trees.",
    )
    args = parser.parse_args()
    patterns = _load_patterns()
    allow = _load_allowlist()

    if args.paths:
        roots = [(REPO_ROOT / p).resolve() for p in args.paths]
    else:
        roots = [REPO_ROOT / r for r in DEFAULT_ROOTS]

    if not _rg_available():
        print(
            "check_modal_http_ban: warning: ripgrep (rg) not found; using slow fallback",
            file=sys.stderr,
        )
        raw_hits = _collect_hits_fallback(patterns, roots)
    else:
        raw_hits = _collect_hits_rg(patterns, roots)

    violations: list[str] = []
    seen: set[tuple[str, str]] = set()
    for rel, line in raw_hits:
        key = (rel, line)
        if key in seen:
            continue
        seen.add(key)
        if _line_violates(rel, line, patterns, allow):
            violations.append(f"{rel}: {line.strip()}")

    if violations:
        print("Modal HTTP ban violations (FR-001):", file=sys.stderr)
        for v in sorted(set(violations)):
            print(v, file=sys.stderr)
        sys.exit(1)
    print("check_modal_http_ban: OK (no qualifying Modal HTTP patterns in scanned paths).")


if __name__ == "__main__":
    main()
