#!/usr/bin/env python3
"""Canonicalize metadata tags across sources and chunks.

Usage:
  uv run python scripts/canonicalize_tags.py --dry-run
  uv run python scripts/canonicalize_tags.py --apply
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.chroma_store import get_chroma_store
from src.utils.tags import normalize_tag_fields

TAG_FIELDS = (
    "tags",
    "location_tags",
    "subject_tags",
    "service_tags",
    "content_type_tags",
    "organization_tags",
    "audience_tags",
)


def _normalize_source_metadata(metadata: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    return normalize_tag_fields(metadata, TAG_FIELDS)


def _normalize_chunk_metadata(metadata: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    return normalize_tag_fields(metadata, TAG_FIELDS)


def run(*, apply: bool, batch_size: int) -> dict[str, Any]:
    store = get_chroma_store()

    sources_scanned = 0
    sources_changed = 0
    chunks_scanned = 0
    chunks_changed = 0

    # Sources
    offset = 0
    while True:
        sources = store.list_sources(limit=batch_size, offset=offset)
        if not sources:
            break

        for source in sources:
            sources_scanned += 1
            url = str(source.get("url") or "")
            title = source.get("title") or url
            metadata = dict(source.get("metadata") or {})
            normalized_metadata, changed = _normalize_source_metadata(metadata)
            if not changed:
                continue
            sources_changed += 1
            if apply and url:
                store.upsert_source(
                    url=url,
                    metadata=normalized_metadata,
                    title=title,
                    is_active=bool(source.get("is_active", True)),
                )

        offset += len(sources)
        if len(sources) < batch_size:
            break

    # Chunks (metadata-only update; preserves embeddings/documents)
    offset = 0
    while True:
        result = store.get_chunks(limit=batch_size, offset=offset)
        ids = result.get("ids") or []
        metadatas = result.get("metadatas") or []
        if not ids:
            break

        update_ids: list[str] = []
        update_metas: list[dict[str, Any]] = []

        for index, chunk_id in enumerate(ids):
            chunks_scanned += 1
            metadata = dict(metadatas[index] or {}) if index < len(metadatas) else {}
            normalized_metadata, changed = _normalize_chunk_metadata(metadata)
            if not changed:
                continue
            chunks_changed += 1
            update_ids.append(str(chunk_id))
            update_metas.append(normalized_metadata)

        if apply and update_ids:
            store.chunks().update(ids=update_ids, metadatas=update_metas)

        offset += len(ids)
        if len(ids) < batch_size:
            break

    return {
        "apply": apply,
        "batch_size": batch_size,
        "tag_fields": list(TAG_FIELDS),
        "sources_scanned": sources_scanned,
        "sources_changed": sources_changed,
        "chunks_scanned": chunks_scanned,
        "chunks_changed": chunks_changed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonicalize bilingual metadata tags")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Apply updates")
    mode.add_argument("--dry-run", action="store_true", help="Preview updates without writing")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    apply = bool(args.apply)
    if not args.apply and not args.dry_run:
        apply = False

    try:
        summary = run(apply=apply, batch_size=max(1, int(args.batch_size)))
        print(json.dumps(summary, indent=2))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": "Ensure Chroma is running and CHROMA_HOST/CHROMA_PORT are reachable before running this migration.",
                },
                indent=2,
            )
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
