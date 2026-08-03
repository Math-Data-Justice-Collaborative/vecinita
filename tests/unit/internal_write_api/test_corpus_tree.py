"""T110.2 — nested source derivation + corpus tree builder (F61 / TC-204)."""

from __future__ import annotations

from pathlib import Path
from typing import Final, cast
from uuid import uuid4

import yaml
from vecinita_ingest.nested_source import derive_nested_source
from vecinita_internal_write_api.corpus_tree import build_corpus_tree
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import json_list, json_str

_SPEC = Path(__file__).resolve().parents[3] / "openapi" / "internal-write.yaml"
_MIN_DOCS: Final[int] = 2


def _spec() -> JsonObject:
    loaded = cast("object", yaml.safe_load(_SPEC.read_text(encoding="utf-8")))
    return as_json_object(loaded)


def test_derive_nested_source_from_url() -> None:
    """URL path yields domain + directory source_path (AC-SC11)."""
    nested = derive_nested_source("https://tree.example.com/guides/a.html")
    assert nested.source_domain == "tree.example.com"
    assert nested.source_path in {"/guides", "guides"}
    assert nested.canonical_url.startswith("https://tree.example.com/guides/a.html")
    assert nested.parent_url is not None
    assert "guides" in nested.parent_url


def test_build_corpus_tree_domain_path_document_nesting() -> None:
    """Builder nests domain → path → document with nested-source fields."""
    suffix = uuid4()
    rows: list[JsonObject] = [
        {
            "id": uuid4(),
            "url": f"https://tree.example.com/guides/a-{suffix}.html",
            "source_domain": None,
            "source_path": None,
            "parent_url": None,
            "canonical_url": None,
        },
        {
            "id": uuid4(),
            "url": f"https://tree.example.com/guides/b-{suffix}.html",
            "source_domain": None,
            "source_path": None,
            "parent_url": None,
            "canonical_url": None,
        },
        {
            "id": uuid4(),
            "url": f"https://other.example.org/index-{suffix}.html",
            "source_domain": None,
            "source_path": None,
            "parent_url": None,
            "canonical_url": None,
        },
    ]
    tree = build_corpus_tree(rows)
    domains = {root.label for root in tree.roots}
    assert "tree.example.com" in domains
    example = next(root for root in tree.roots if root.label == "tree.example.com")
    assert example.kind == "domain"
    assert example.children
    guides = example.children[0]
    assert guides.kind == "path"
    assert guides.label == "guides"
    assert len(guides.children) >= _MIN_DOCS
    for doc in guides.children:
        assert doc.kind == "document"
        assert doc.source_domain == "tree.example.com"
        assert doc.source_path in {"/guides", "guides"}
        assert doc.url is not None


def test_openapi_corpus_tree_route_and_schemas() -> None:
    """OpenAPI documents GET /corpus/tree + CorpusTreeResponse (TP3)."""
    paths = as_json_object(_spec()["paths"])
    assert "/corpus/tree" in paths
    components = as_json_object(_spec()["components"])
    schemas = as_json_object(components["schemas"])
    assert "CorpusTreeResponse" in schemas
    assert "TreeNode" in schemas
    tree_node = as_json_object(schemas["TreeNode"])
    props = as_json_object(tree_node["properties"])
    assert "source_domain" in props
    assert "source_path" in props
    summary = as_json_object(schemas["DocumentSummary"])
    summary_props = as_json_object(summary["properties"])
    assert "source_domain" in summary_props
    upsert = as_json_object(schemas["DocumentUpsert"])
    upsert_props = as_json_object(upsert["properties"])
    assert "canonical_url" in upsert_props


def test_build_corpus_tree_root_filter() -> None:
    """Optional root query limits domains."""
    rows: list[JsonObject] = [
        {"id": uuid4(), "url": "https://keep.example.com/docs/a.html"},
        {"id": uuid4(), "url": "https://drop.example.org/docs/b.html"},
    ]
    tree = build_corpus_tree(rows, root="keep.example.com")
    labels = {json_str(as_json_object(root.model_dump()), "label") for root in tree.roots}
    assert labels == {"keep.example.com"}
    # smoke that children serialize
    roots = json_list(as_json_object({"roots": [r.model_dump() for r in tree.roots]}), "roots")
    assert roots


def test_build_corpus_tree_root_url_document_label_and_empty_path() -> None:
    """Root URL documents use '/' label and attach directly under the domain."""
    doc_id = uuid4()
    tree = build_corpus_tree(
        [{"id": str(doc_id), "url": "https://root.example.com/", "source_path": "/"}],
    )
    assert len(tree.roots) == 1
    domain = tree.roots[0]
    assert domain.label == "root.example.com"
    assert domain.children is not None
    assert len(domain.children) == 1
    doc = domain.children[0]
    assert doc.kind == "document"
    assert doc.label == "/"
    assert doc.id == str(doc_id)


def test_build_corpus_tree_root_prefix_keeps_matching_domain() -> None:
    """Root filter keeps domains that start with the root prefix."""
    rows: list[JsonObject] = [
        {"id": uuid4(), "url": "https://docs.keep.example.com/a.html"},
        {"id": uuid4(), "url": "https://other.example.org/b.html"},
    ]
    tree = build_corpus_tree(rows, root="docs.keep.example.com")
    labels = {root.label for root in tree.roots}
    assert labels == {"docs.keep.example.com"}


def test_build_corpus_tree_ignores_non_string_optional_fields() -> None:
    """Non-string nested-source columns fall back to URL derivation."""
    tree = build_corpus_tree(
        [
            {
                "id": uuid4(),
                "url": "https://cast.example.com/path/doc.html",
                "source_domain": 123,
                "source_path": False,
                "parent_url": 1.5,
                "canonical_url": None,
            }
        ],
    )
    assert tree.roots[0].label == "cast.example.com"
    path = tree.roots[0].children[0]
    assert path.kind == "path"
    assert path.label == "path"
