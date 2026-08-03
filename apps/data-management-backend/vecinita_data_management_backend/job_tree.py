"""Build nested job result trees from job URLs (F60 / ADR-045)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from vecinita_shared_schemas.data_management import JobTreeResponse, TreeNode

if TYPE_CHECKING:
    from vecinita_data_management_backend.store import JobRecord


def _path_segments(path: str) -> list[str]:
    return [part for part in path.split("/") if part]


def build_job_tree(record: JobRecord) -> JobTreeResponse:
    """Nest job URLs as domain → path → document nodes."""
    # domain -> directory path key -> document nodes
    by_domain: dict[str, dict[str, list[TreeNode]]] = {}

    for url in record.urls:
        parsed = urlparse(url)
        domain = parsed.netloc.lower() or "unknown"
        segments = _path_segments(parsed.path)
        if segments:
            *dir_parts, file_label = segments
            path_key = "/".join(dir_parts)
            doc_label = file_label
        else:
            path_key = ""
            doc_label = "/"

        doc = TreeNode(
            id=f"document:{url}",
            kind="document",
            label=doc_label,
            url=url,
            status=record.status,
        )
        by_domain.setdefault(domain, {}).setdefault(path_key, []).append(doc)

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

    return JobTreeResponse(job_id=record.job_id, roots=roots)
