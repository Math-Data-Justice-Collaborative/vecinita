#!/usr/bin/env python3
"""Sync selected docs/ markdown to the GitHub Wiki git repository.

Manifest: docs/wiki-manifest.json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "docs" / "wiki-manifest.json"

MARKDOWN_LINK = re.compile(r"\]\(([^)#]+)(#[^)]+)?\)")


class PageEntry(TypedDict):
    source: str
    wiki: str


class Section(TypedDict, total=False):
    id: str
    title: str
    pages: list[PageEntry]
    glob: dict[str, str]


class Manifest(TypedDict, total=False):
    version: int
    home: dict[str, str | int]
    sections: list[Section]
    operator_only_sections: list[Section]
    exclude_from_wiki: list[str]


@dataclass(frozen=True)
class WikiPage:
    source: Path
    wiki: str


def load_manifest(path: Path) -> Manifest:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"manifest must be a JSON object: {path}"
        raise TypeError(msg)
    return raw  # type: ignore[return-value]


def expand_sections(sections: list[Section]) -> list[WikiPage]:
    pages: list[WikiPage] = []
    for section in sections:
        pages.extend(
            WikiPage(source=REPO_ROOT / entry["source"], wiki=entry["wiki"])
            for entry in section.get("pages", [])
        )
        glob_spec = section.get("glob")
        if glob_spec is None:
            continue
        pattern = glob_spec["pattern"]
        prefix = glob_spec.get("wiki_prefix", "")
        for match in sorted(REPO_ROOT.glob(pattern)):
            if match.name == "README.md":
                continue
            wiki_name = f"{prefix}{match.stem}" if prefix else match.stem
            pages.append(WikiPage(source=match, wiki=wiki_name))
    return pages


def collect_pages(manifest: Manifest, *, include_operator: bool) -> list[WikiPage]:
    pages = expand_sections(manifest.get("sections", []))
    if include_operator:
        pages.extend(expand_sections(manifest.get("operator_only_sections", [])))
    seen: set[str] = set()
    unique: list[WikiPage] = []
    for page in pages:
        key = page.wiki
        if key in seen:
            continue
        seen.add(key)
        unique.append(page)
    return unique


def source_to_wiki_map(pages: list[WikiPage]) -> dict[Path, str]:
    mapping: dict[Path, str] = {}
    for page in pages:
        mapping[page.source.resolve()] = page.wiki
        with contextlib.suppress(ValueError):
            mapping[page.source.resolve().relative_to(REPO_ROOT)] = page.wiki
    return mapping


def resolve_link_target(raw_target: str, source_file: Path) -> Path | None:
    target = raw_target.strip()
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    if target.startswith("/"):
        candidate = REPO_ROOT / target.lstrip("/")
    else:
        candidate = (source_file.parent / target).resolve()
    if candidate.suffix != ".md":
        candidate = candidate.with_suffix(".md")
    return candidate


def rewrite_markdown_links(content: str, source_file: Path, link_map: dict[Path, str]) -> str:
    repo_blob_base = "https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/"

    def replace_link(match: re.Match[str]) -> str:
        raw_target = match.group(1)
        anchor = match.group(2) or ""
        resolved = resolve_link_target(raw_target, source_file)
        if resolved is None:
            return match.group(0)
        wiki_page = link_map.get(resolved.resolve())
        if wiki_page is None:
            try:
                rel = resolved.resolve().relative_to(REPO_ROOT)
                wiki_page = link_map.get(rel)
            except ValueError:
                wiki_page = None
        if wiki_page is not None:
            return f"]({wiki_page}{anchor})"
        try:
            rel_path = resolved.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return match.group(0)
        return f"]({repo_blob_base}{rel_path}{anchor})"

    return MARKDOWN_LINK.sub(replace_link, content)


def render_home(manifest: Manifest, pages: list[WikiPage]) -> str:
    home_spec = manifest.get("home", {})
    readme_path = REPO_ROOT / str(home_spec.get("source_readme", "README.md"))
    readme_body = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""

    lines = [
        "# Vecinita Wiki",
        "",
        "> Auto-synced from [`docs/`](https://github.com/Math-Data-Justice-Collaborative/vecinita/tree/main/docs) on push to `main`.",
        "> Edit source files in the repo — not this wiki directly (changes will be overwritten).",
        "",
    ]

    if readme_body:
        # Strip the top-level title from README to avoid duplicate H1.
        readme_lines = readme_body.splitlines()
        if readme_lines and readme_lines[0].startswith("# "):
            readme_lines = readme_lines[1:]
        lines.extend(readme_lines)
        lines.append("")

    lines.extend(["## Wiki index", ""])
    for section in manifest.get("sections", []):
        lines.append(f"### {section.get('title', section.get('id', 'Section'))}")
        lines.extend(
            f"- [{entry['wiki'].split('/')[-1].replace('-', ' ')}]({entry['wiki']})"
            for entry in section.get("pages", [])
        )
        glob_spec = section.get("glob")
        if glob_spec is not None:
            pattern = glob_spec["pattern"]
            prefix = glob_spec.get("wiki_prefix", "")
            adr_count = len(list(REPO_ROOT.glob(pattern)))
            lines.append(
                f"- [ADR index](ADR-Index) — {adr_count} decision records under `{prefix}`"
            )
        lines.append("")

    lines.append(f"_Last sync covers {len(pages)} wiki pages._")
    return "\n".join(lines).rstrip() + "\n"


def render_sidebar(manifest: Manifest, *, include_operator: bool) -> str:
    lines = ["### Vecinita", "- [Home](Home)", ""]
    for section in manifest.get("sections", []):
        lines.append(f"**{section.get('title', '')}**")
        for entry in section.get("pages", []):
            label = entry["wiki"].split("/")[-1].replace("-", " ")
            lines.append(f"- [{label}]({entry['wiki']})")
        if section.get("glob"):
            lines.append("- [ADR index](ADR-Index)")
        lines.append("")
    if include_operator:
        lines.append("**Operator (restricted)**")
        for section in manifest.get("operator_only_sections", []):
            for entry in section.get("pages", []):
                label = entry["wiki"].split("/")[-1].replace("-", " ")
                lines.append(f"- [{label}]({entry['wiki']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_wiki_tree(
    out_dir: Path, pages: list[WikiPage], manifest: Manifest, *, include_operator: bool
) -> None:
    if out_dir.exists():
        for child in out_dir.iterdir():
            if child.is_file() and child.suffix == ".md":
                child.unlink()
            elif child.is_dir():
                import shutil

                shutil.rmtree(child)
    out_dir.mkdir(parents=True, exist_ok=True)

    link_map = source_to_wiki_map(pages)
    for page in pages:
        if not page.source.is_file():
            print(f"WARN: missing source {page.source}", file=sys.stderr)
            continue
        body = page.source.read_text(encoding="utf-8")
        body = rewrite_markdown_links(body, page.source, link_map)
        target = out_dir / f"{page.wiki}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    (out_dir / "Home.md").write_text(render_home(manifest, pages), encoding="utf-8")
    (out_dir / "_Sidebar.md").write_text(
        render_sidebar(manifest, include_operator=include_operator),
        encoding="utf-8",
    )


def git_push_wiki(wiki_dir: Path, *, remote_url: str, message: str) -> None:
    env = {"GIT_TERMINAL_PROMPT": "0"}
    subprocess.run(["git", "init"], cwd=wiki_dir, check=True, env=env)
    subprocess.run(
        ["git", "config", "user.name", "github-actions[bot]"], cwd=wiki_dir, check=True, env=env
    )
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        cwd=wiki_dir,
        check=True,
        env=env,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", remote_url], cwd=wiki_dir, check=True, env=env
    )
    subprocess.run(["git", "add", "-A"], cwd=wiki_dir, check=True, env=env)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=wiki_dir,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    if not status.stdout.strip():
        print("Wiki already up to date — no commit needed.")
        return
    subprocess.run(["git", "commit", "-m", message], cwd=wiki_dir, check=True, env=env)
    subprocess.run(
        ["git", "push", "--force", "origin", "HEAD:master"], cwd=wiki_dir, check=True, env=env
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / ".wiki-build")
    parser.add_argument(
        "--include-operator",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument("--dry-run", action="store_true", help="Build wiki tree only; do not push.")
    parser.add_argument(
        "--remote-url", default="", help="Wiki git remote (required unless --dry-run)."
    )
    parser.add_argument("--message", default="Sync docs from repository")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = load_manifest(args.manifest)
    pages = collect_pages(manifest, include_operator=args.include_operator)

    write_wiki_tree(args.out_dir, pages, manifest, include_operator=args.include_operator)
    print(f"Built {len(pages)} wiki pages in {args.out_dir}")

    if args.dry_run:
        return 0
    if not args.remote_url:
        print("ERROR: --remote-url is required when not using --dry-run", file=sys.stderr)
        return 1
    git_push_wiki(args.out_dir, remote_url=args.remote_url, message=args.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
