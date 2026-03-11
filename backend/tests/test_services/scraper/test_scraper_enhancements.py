import os
import types
from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestLinkExtraction:
    @patch('src.services.scraper.utils.requests.get')
    def test_extract_outbound_links_filters_and_normalizes(self, mock_get):
        from src.services.scraper.utils import extract_outbound_links

        html = '''
        <html><body>
          <a href="/relative">Rel</a>
          <a href="https://allowed.com/x">Abs</a>
          <a href="#top">Frag</a>
          <a href="mailto:info@example.com">Mail</a>
          <a href="tel:+15551234567">Tel</a>
          <a href="javascript:void(0)">JS</a>
          <a href="https://facebook.com/somepage">Social</a>
          <a href="/relative">Duplicate</a>
        </body></html>
        '''
        mock_resp = Mock()
        mock_resp.text = html
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        base = 'https://example.com/base/page'
        links = extract_outbound_links(base)
        assert 'https://example.com/relative' in links
        assert 'https://allowed.com/x' in links
        # filtered out
        assert not any(l.startswith('#') for l in links)
        assert not any(l.startswith('mailto:') for l in links)
        assert not any(l.startswith('tel:') for l in links)
        assert not any('facebook.com' in l for l in links)
        # deduped
        assert links.count('https://example.com/relative') == 1

        # same-domain-only
        links_same = extract_outbound_links(base, same_domain_only=True)
        assert links_same == ['https://example.com/relative']


@pytest.mark.unit
class TestUploaderPayload:
    def test_loader_type_stored_in_metadata_not_top_level(self, monkeypatch):
        from src.services.scraper.uploader import DatabaseUploader, DocumentChunk

        captured = {"rows": []}

        class MockChromaStore:
            def heartbeat(self):
                return True

            def upsert_source(self, **kwargs):
                return None

            def query_source_metadata(self, *args, **kwargs):
                return {}

            def list_tags(self):
                return []

            def upsert_chunks(self, rows):
                captured["rows"].extend(rows)
                return len(rows)

        monkeypatch.setattr("src.services.scraper.uploader.get_chroma_store", lambda: MockChromaStore())

        # Avoid loading sentence-transformers by bypassing embeddings
        monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
        monkeypatch.setenv('SUPABASE_KEY', 'test-key')
        monkeypatch.setenv('VECTOR_SYNC_ENABLED', 'false')

        uploader = DatabaseUploader(use_local_embeddings=False)

        # Monkeypatch embedding generation
        def fake_gen(texts):
            return [[0.0, 0.1, 0.2]] * len(texts)
        uploader._generate_embeddings = fake_gen  # type: ignore

        chunks = [
            DocumentChunk(
                content='hello world',
                source_url='https://example.com',
                chunk_index=0,
                total_chunks=1,
                loader_type='Unstructured',
                metadata={'foo': 'bar'},
            )
        ]

        uploaded, failed = uploader.upload_chunks(
            chunks=[{'text': 'hello world', 'metadata': {'foo': 'bar'}}],
            source_identifier='https://example.com',
            loader_type='Unstructured',
        )

        assert uploaded == 1
        assert failed == 0
        assert captured["rows"], "Expected at least one upserted row"
        assert 'loader_type' not in captured["rows"][0]
        assert 'metadata' in captured["rows"][0]
        assert captured["rows"][0]['metadata'].get('loader_type') == 'Unstructured'


@pytest.mark.unit
class TestFallbackProcessing:
    @patch('time.sleep', lambda x: None)
    def test_playwright_fallback_when_no_chunks(self, monkeypatch, tmp_path):
        from src.services.scraper.scraper import VecinaScraper

        output = tmp_path / 'out.txt'
        failed = tmp_path / 'failed.txt'

        # Don't enable stream_mode to avoid uploader initialization
        scraper = VecinaScraper(output_file=str(
            output), failed_log=str(failed), stream_mode=False)

        # Mock loader to be called twice: first normal, then with Playwright
        calls = {'count': 0}

        def fake_load_url(url, failed_log, force_loader=None):
            calls['count'] += 1
            if calls['count'] == 1:
                # Return some doc but processing will report 0 chunks
                doc = types.SimpleNamespace(
                    page_content='nav footer', metadata={})
                return [doc], 'Unstructured URL Loader', True
            else:
                # Fallback returns keepable content
                doc = types.SimpleNamespace(
                    page_content='This is real content.', metadata={})
                return [doc], 'Playwright (JavaScript rendering)', True

        scraper.loader.load_url = fake_load_url  # type: ignore

        # Mock processor to first return 0 chunks, then 2
        proc_calls = {'count': 0}

        def fake_process_documents(docs, source_identifier, loader_type, output_file=None, links_file=None):
            proc_calls['count'] += 1
            if proc_calls['count'] == 1:
                return 0, []
            else:
                return 2, ['https://example.com/a']

        scraper.processor.process_documents = fake_process_documents  # type: ignore

        # Run just the single URL through the private helper to avoid overall loop
        scraper._process_single_url('https://example.com')

        # Assert fallback path succeeded
        assert 'https://example.com' in scraper.successful_sources
        assert scraper.stats['successful'] == 1
        assert scraper.stats['total_chunks'] == 2
        assert scraper.stats['total_links'] == 1
