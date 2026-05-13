"""Tests for indexing worker Modal app."""
import hashlib


def test_app_defined():
    from main import app
    assert app.name == "vecinita-indexing-worker"


def test_content_hash():
    from main import _content_hash
    text = "hello world"
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert _content_hash(text) == expected


def test_all_modes_exist():
    from main import index_single_doc, index_batch, selective_reindex, full_rebuild
    assert index_single_doc is not None
    assert index_batch is not None
    assert selective_reindex is not None
    assert full_rebuild is not None
