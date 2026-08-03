"""Build nested corpus trees from document rows (F61 / ADR-045)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from vecinita_ingest.nested_source import derive_nested_source
from vecinita_shared_schemas.data_management import CorpusTreeResponse, TreeNode

if TYPE_CHECKING:
    from collections.abc import Sequence

    from vecinita_shared_schemas.json_types import JsonObject


def _row_str(row: JsonObject, key: str) -> str | None:
    value = row.get(key)
    return value if isinstance(value, str) else None


def _row_uuid(row: JsonObject, key: str) -> UUID:
    value = row[key]
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def build_corpus_tree(
    rows: Sequence[JsonObject],
    *,
    root: str | None = None,
) -> CorpusTreeResponse:
    """Nest documents as domain → path → document (chunks lazy / omitted)."""
    # domain -> directory path key -> document nodes
    by_domain: dict[str, dict[str, list[TreeNode]]] = {}

    for row in rows:
        url = _row_str(row, "url") or ""
        nested = derive_nested_source(
            url,
            parent_url=_row_str(row, "parent_url"),
            source_domain=_row_str(row, "source_domain"),
            source_path=_row_str(row, "source_path"),
            canonical_url=_row_str(row, "canonical_url"),
        )
        if root:
            root_l = root.lower().rstrip("/")
            if nested.source_domain != root_l and not (
                nested.source_domain.startswith(root_l)
                or f"{nested.source_domain}{nested.source_path}".startswith(root_l)
            ):
                continue

        path_key = nested.source_path.strip("/")
        doc_id = _row_uuid(row, "id")
        label = url.rsplit("/", maxsplit=1)[-1] if "/" in url.rstrip("/") else url
        if not label:
            label = "/"
        doc = TreeNode(
            id=str(doc_id),
            kind="document",
            label=label,
            url=url,
            source_domain=nested.source_domain,
            source_path=nested.source_path,
            parent_url=nested.parent_url,
            canonical_url=nested.canonical_url,
        )
        by_domain.setdefault(nested.source_domain, {}).setdefault(path_key, []).append(doc)

    roots: list[TreeNode] = []
    for domain in sorted(by_domain):
        path_map = by_domain[domain]
        children: list[TreeNode] = []
        doc_count = 0
        for path_key in sorted(path_map):
            docs = path_map[path_key]
            doc_count += len(docs)
            if path_key:
                label = path_key.rsplit("/", maxsplit=1)[-1]
                children.append(
                    TreeNode(
                        id=f"path:{domain}/{path_key}",
                        kind="path",
                        label=label,
                        children=list(docs),
                    )
                )
            else:
                children.extend(docs)
        roots.append(
            TreeNode(
                id=f"domain:{domain}",
                kind="domain",
                label=domain,
                counts={"documents": doc_count},
                children=children,
            )
        )

    return CorpusTreeResponse(roots=roots)
