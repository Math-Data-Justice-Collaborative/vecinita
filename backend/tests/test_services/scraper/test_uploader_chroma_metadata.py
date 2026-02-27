import sys
import types

import pytest
from unittest.mock import Mock, patch

# Avoid importing heavy optional crypto dependencies through src.utils.__init__
if "src.utils.supabase_embeddings" not in sys.modules:
    fake_supabase_embeddings = types.ModuleType("src.utils.supabase_embeddings")

    class _FakeSupabaseEmbeddings:
        pass

    fake_supabase_embeddings.SupabaseEmbeddings = _FakeSupabaseEmbeddings
    sys.modules["src.utils.supabase_embeddings"] = fake_supabase_embeddings

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
    assert "tags" in row["metadata"]
    assert row["metadata"].get("tags_en")
    assert row["metadata"].get("tags_es")


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
    assert "healthcare" in tags
    assert "insurance" in tags
    assert "legal assistance" in tags
    assert "how-to" in tags
    assert "nonprofit" in tags
    assert "families" in tags

    assert row["metadata"]["location_tags"] == ["providence", "rhode island"]
    assert row["metadata"]["subject_tags"] == ["healthcare", "insurance"]
    assert row["metadata"]["service_tags"] == ["legal assistance"]
    assert row["metadata"]["content_type_tags"] == ["how-to", "guide"]
    assert row["metadata"]["organization_tags"] == ["nonprofit", "coalition"]
    assert row["metadata"]["audience_tags"] == ["families", "immigrants"]


def test_upload_chunks_infers_source_tags_and_bilingual_fields_without_llm():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.deepseek_tagger = None

    uploaded, failed = uploader.upload_chunks(
        chunks=[
            {
                "text": "Ofrecemos ayuda de inmigración y asistencia de vivienda para familias.",
                "metadata": {},
            }
        ],
        source_identifier="https://example.org/servicios",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    row = uploader.chroma_store.upsert_chunks.call_args[0][0][0]

    tags = row["metadata"].get("tags", [])
    assert "immigration" in tags
    assert "housing assistance" in tags or "housing" in tags
    assert "tags_en" in row["metadata"]
    assert "tags_es" in row["metadata"]
    assert "inmigracion" in row["metadata"]["tags_es"]


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


def test_init_tagger_uses_groq_when_deepseek_unavailable(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_TAG_ENHANCEMENT", "true")
    monkeypatch.setenv("LLM_TAG_PROVIDER", "auto")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GROQ_TAG_MODEL", "llama-3.1-8b-instant")

    with patch.object(DatabaseUploader, "_init_embeddings"), patch.object(DatabaseUploader, "_init_supabase"):
        with patch("src.services.scraper.uploader.GROQ_TAGGING_AVAILABLE", True), patch("src.services.scraper.uploader.ChatGroq") as mock_chat_groq:
            llm = Mock()
            structured_tagger = Mock()
            llm.with_structured_output.return_value = structured_tagger
            mock_chat_groq.return_value = llm

            uploader = DatabaseUploader(use_local_embeddings=False)

    assert uploader.deepseek_tagger is structured_tagger
    assert uploader.deepseek_raw_model is llm
    mock_chat_groq.assert_called_once()


def test_upload_chunks_syncs_to_supabase_with_retry_in_degraded_mode():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.vector_sync_enabled = True
    uploader.vector_sync_degraded_mode = True
    uploader.vector_sync_retry_max = 2
    uploader.vector_sync_retry_delay_seconds = 1

    sync_table = Mock()
    sync_table.upsert.return_value = sync_table
    sync_table.execute.side_effect = [Exception("temporary sync error"), {"data": []}]
    uploader.supabase_client = Mock()
    uploader.supabase_client.table.return_value = sync_table

    with patch("src.services.scraper.uploader.time.sleep", return_value=None):
        uploaded, failed = uploader.upload_chunks(
            chunks=[{"text": "community services", "metadata": {}}],
            source_identifier="https://example.org/help",
            loader_type="playwright",
        )

    assert uploaded == 1
    assert failed == 0
    assert sync_table.execute.call_count == 2
    assert uploader.vector_sync_pending_rows == []


def test_upload_chunks_queues_supabase_sync_rows_when_all_retries_fail():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.vector_sync_enabled = True
    uploader.vector_sync_degraded_mode = True
    uploader.vector_sync_retry_max = 2
    uploader.vector_sync_retry_delay_seconds = 1

    sync_table = Mock()
    sync_table.upsert.return_value = sync_table
    sync_table.execute.side_effect = Exception("persistent sync error")
    uploader.supabase_client = Mock()
    uploader.supabase_client.table.return_value = sync_table

    with patch("src.services.scraper.uploader.time.sleep", return_value=None):
        uploaded, failed = uploader.upload_chunks(
            chunks=[{"text": "food assistance", "metadata": {}}],
            source_identifier="https://example.org/food",
            loader_type="playwright",
        )

    assert uploaded == 1
    assert failed == 0
    assert len(uploader.vector_sync_pending_rows) == 1


def test_upload_chunks_strict_sync_mode_fails_when_supabase_unavailable():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.vector_sync_enabled = True
    uploader.vector_sync_degraded_mode = False
    uploader.vector_sync_retry_max = 1

    sync_table = Mock()
    sync_table.upsert.return_value = sync_table
    sync_table.execute.side_effect = Exception("sync hard failure")
    uploader.supabase_client = Mock()
    uploader.supabase_client.table.return_value = sync_table

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "strict sync chunk", "metadata": {}}],
        source_identifier="https://example.org/strict",
        loader_type="playwright",
    )

    assert uploaded == 0
    assert failed == 1


def test_upload_chunks_flushes_pending_sync_queue_before_new_batch():
    uploader = _make_uploader()
    uploader._generate_embeddings = Mock(return_value=[[0.1, 0.2, 0.3]])
    uploader.chroma_store.upsert_chunks = Mock(return_value=1)
    uploader.vector_sync_enabled = True
    uploader.vector_sync_degraded_mode = True
    uploader.vector_sync_retry_max = 1
    uploader.vector_sync_pending_rows = [
        {
            "id": "queued-1",
            "content": "queued content",
            "source_url": "https://example.org/queued",
            "source_domain": "example.org",
            "chunk_index": 0,
            "total_chunks": 1,
            "chunk_size": 12,
            "document_title": "",
            "metadata": {},
            "embedding": [0.1, 0.2],
            "processing_status": "completed",
            "is_processed": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "scraped_at": "2026-01-01T00:00:00+00:00",
        }
    ]

    sync_table = Mock()
    sync_table.upsert.return_value = sync_table
    sync_table.execute.side_effect = [{"data": []}, {"data": []}]
    uploader.supabase_client = Mock()
    uploader.supabase_client.table.return_value = sync_table

    uploaded, failed = uploader.upload_chunks(
        chunks=[{"text": "new chunk", "metadata": {}}],
        source_identifier="https://example.org/new",
        loader_type="playwright",
    )

    assert uploaded == 1
    assert failed == 0
    assert uploader.vector_sync_pending_rows == []
    assert sync_table.execute.call_count == 2
