"""Tests for embedding worker Modal app."""


def test_app_defined():
    from main import app

    assert app.name == "vecinita-embedding-worker"


def test_embed_documents_function_exists():
    from main import embed_documents

    assert embed_documents is not None


def test_embed_query_function_exists():
    from main import embed_query

    assert embed_query is not None
