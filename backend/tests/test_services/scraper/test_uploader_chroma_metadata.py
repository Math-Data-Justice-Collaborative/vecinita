import pytest
from unittest.mock import Mock, patch

from src.services.scraper.uploader import DatabaseUploader

pytestmark = pytest.mark.unit


def _make_uploader():
    with patch.object(DatabaseUploader, "_init_embeddings"), patch.object(DatabaseUploader, "_init_supabase"), patch.object(DatabaseUploader, "_init_deepseek_tagger"):
        uploader = DatabaseUploader(use_local_embeddings=False)
    uploader.chroma_store = Mock()
    uploader.chroma_store.list_sources.return_value = []
    uploader.chroma_store.get_source.return_value = None
    uploader.deepseek_tagger = None
    return uploader


def test_upload_chunks_omits_empty_tags_and_sets_source_locator():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "community services", "metadata": {"tags": []}}],
        source_identifier="https://sub.example.com/chat/help",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0

    rows = uploader.chroma_store.upsert_chunks.call_args[0][0]
    assert len(rows) == 1
    row = rows[0]
    assert row["source_url"] == "https://sub.example.com/chat/help"
    assert row["source_domain"] == "sub.example.com/chat/help"
    assert "tags" not in row["metadata"]


def test_chunk_id_is_stable_for_upsert_updates():
    uploader = _make_uploader()

    id_a = uploader._build_chunk_id("https://wrwc.org/", 3)
    id_b = uploader._build_chunk_id("https://wrwc.org/", 3)
    id_c = uploader._build_chunk_id("https://wrwc.org/", 4)

    assert id_a == id_b
    assert id_a != id_c


def test_upload_chunks_uses_deepseek_structured_tags_when_available():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.deepseek_tagger = Mock(
        invoke=Mock(
            return_value={
                "tags": ["Housing", "Benefits", "Community Resources"],
                "document_title": "WRWC Programs",
                "source_summary": "Support services and local programs.",
            }
        )
    )

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "We provide housing and benefits support.", "metadata": {}}],
        source_identifier="https://wrwc.org/programs",
        loader_type="unstructured",
    )

    assert uploaded == 1
    assert failed == 0

    row = uploader.chroma_store.upsert_chunks.call_args[0][0][0]
    assert row["metadata"]["tags"] == ["housing", "benefits", "community resources"]
    assert row["metadata"]["document_title"] == "WRWC Programs"


def test_upload_chunks_merges_deepseek_facets_into_search_tags_and_metadata():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.deepseek_tagger = Mock(
        invoke=Mock(
            return_value={
                "tags": ["community support"],
                "location_tags": ["Providence", "Rhode Island"],
                "subject_tags": ["health", "insurance"],
                "service_tags": ["legal assistance"],
                "content_type_tags": ["how-to", "guide"],
                "organization_tags": ["nonprofit", "coalition"],
                "audience_tags": ["families", "immigrants"],
                "document_title": "Community Programs",
                "source_summary": "Programs and assistance resources",
            }
        )
    )

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "Programs for health and legal support.", "metadata": {}}],
        source_identifier="https://example.org/community/help",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    row = uploader.chroma_store.upsert_chunks.call_args[0][0][0]

    tags = row["metadata"]["tags"]
    assert "community support" in tags
    assert "providence" in tags
    assert "health" in tags
    assert "insurance" in tags
    assert "legal assistance" in tags
    assert "how-to" in tags
    assert "nonprofit" in tags
    assert "families" in tags

    assert row["metadata"]["location_tags"] == ["providence", "rhode island"]
    assert row["metadata"]["subject_tags"] == ["health", "insurance"]
    assert row["metadata"]["service_tags"] == ["legal assistance"]
    assert row["metadata"]["content_type_tags"] == ["how-to", "guide"]
    assert row["metadata"]["organization_tags"] == ["nonprofit", "coalition"]
    assert row["metadata"]["audience_tags"] == ["families", "immigrants"]


def test_upload_chunks_uses_deepseek_json_fallback_when_response_format_unavailable():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.deepseek_tagger = Mock(invoke=Mock(side_effect=Exception("response_format type unavailable")))
    uploader.deepseek_raw_model = Mock(
        invoke=Mock(
            return_value=Mock(
                content='{"tags": ["Housing", "Legal Aid"], "document_title": "WRWC Help", "source_summary": "Local support resources."}'
            )
        )
    )

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "Housing and legal aid support.", "metadata": {}}],
        source_identifier="https://wrwc.org/help",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    row = uploader.chroma_store.upsert_chunks.call_args[0][0][0]
    assert row["metadata"]["tags"] == ["housing", "legal aid"]
    assert row["metadata"]["document_title"] == "WRWC Help"


def test_upload_chunks_reuses_existing_source_tags_with_deepseek_tags():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.chroma_store.get_source.return_value = {
        "id": "https://wrwc.org/help",
        "title": "WRWC Help",
        "metadata": {"tags": ["housing", "families"]},
    }
    uploader.chroma_store.list_sources.return_value = [
        {"url": "https://wrwc.org/help", "tags": ["housing", "families", "benefits"]}
    ]
    uploader.deepseek_tagger = Mock(
        invoke=Mock(
            return_value={
                "tags": ["legal aid"],
                "document_title": "WRWC Help",
                "source_summary": "Local support resources.",
            }
        )
    )

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "Housing and legal aid support.", "metadata": {}}],
        source_identifier="https://wrwc.org/help",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    row = uploader.chroma_store.upsert_chunks.call_args[0][0][0]
    assert row["metadata"]["tags"] == ["housing", "families", "benefits", "legal aid"]
