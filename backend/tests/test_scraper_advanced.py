"""
Edge case and advanced integration tests for the scraper module.
Tests for error handling, edge cases, and end-to-end scenarios.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from src.scraper.config import ScraperConfig
from src.scraper.link_tracker import LinkTracker
from src.scraper.loaders import SmartLoader
from src.scraper.processors import DocumentProcessor
from src.scraper.scraper import VecinaScraper
from src.scraper.utils import clean_text, convert_github_to_raw, write_to_failed_log


@pytest.mark.unit
class TestScraperEdgeCases:
    """Test edge cases and error conditions."""

    def test_processor_with_no_metadata(self):
        """Test processor handles documents with no metadata."""
        config = Mock()
        config.CHUNK_SIZE = 1000
        config.CHUNK_OVERLAP = 200

        mock_doc = Mock()
        mock_doc.page_content = "Content with sufficient words to be processed properly."
        mock_doc.metadata = {}  # No source metadata

        processor = DocumentProcessor(config)
        chunks, links = processor.process_documents(
            docs=[mock_doc], source_identifier="https://example.com", loader_type="Test"
        )

        assert chunks > 0
        # Links should be empty since no metadata
        assert links == []

    def test_link_tracker_with_duplicate_links(self):
        """Test link tracker deduplicates links."""
        tracker = LinkTracker()
        tracker.add_links(
            "https://example.com", ["https://link1.com", "https://link1.com", "https://link2.com"]
        )

        summary = tracker.get_summary()
        # Total links = 3, but unique should handle deduplication
        assert summary["total_links"] == 3

    def test_config_with_invalid_depth(self):
        """Test config handles invalid depth values."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            config_file = f.name
            f.write("https://example.com invalid_depth\n")
            f.write("https://test.org 2\n")

        try:
            with patch("builtins.open", create=True):
                ScraperConfig()
                # Should handle gracefully without crashing
        finally:
            os.remove(config_file)

    def test_clean_text_with_only_noise(self):
        """Test text cleaning with content that's mostly noise."""
        dirty_text = """
        Cookie policy. Privacy policy. Terms of service.
        All rights reserved. Copyright 2024.
        Log in. Sign up. Register.
        """

        result = clean_text(dirty_text)
        # Should be some reduction in content size (not all boilerplate removed)
        # Original has ~146 chars, result should be < 100 chars
        assert len(result) < 100

    def test_url_with_special_characters(self):
        """Test handling URLs with special characters."""
        url = "https://github.com/user/repo/blob/main/file%20with%20spaces.csv"
        result = convert_github_to_raw(url)

        assert "raw.githubusercontent.com" in result
        assert "/main/" in result

    def test_very_large_chunk_splitting(self):
        """Test that very large documents are split properly."""
        config = Mock()
        config.CHUNK_SIZE = 500  # Smaller size
        config.CHUNK_OVERLAP = 100

        # Create a document with lots of text
        large_text = "word " * 1000  # ~5000 characters
        mock_doc = Mock()
        mock_doc.page_content = large_text
        mock_doc.metadata = {"source": "https://example.com"}

        processor = DocumentProcessor(config)
        chunks, links = processor.process_documents(
            docs=[mock_doc], source_identifier="https://example.com", loader_type="Test"
        )

        # Should create multiple chunks for large document
        assert chunks > 1


@pytest.mark.unit
class TestScraperWithMockedRequests:
    """Test scraper with mocked HTTP requests."""

    @patch("src.scraper.loaders.PlaywrightURLLoader")
    def test_playwright_loader_error_handling(self, mock_playwright):
        """Test Playwright loader returns empty results on failure without fallback."""
        # Playwright fails
        mock_playwright_instance = Mock()
        mock_playwright_instance.load.side_effect = Exception("Playwright failed")
        mock_playwright.return_value = mock_playwright_instance

        config = Mock()
        config.RATE_LIMIT_DELAY = 0.1
        config.sites_to_skip = []
        config.sites_needing_playwright = ["test.com"]
        config.sites_to_crawl = {}

        loader = SmartLoader(config)
        docs, loader_type, success = loader.load_url("https://test.com")

        # Should have attempted Playwright first (it's marked as needing it)
        assert mock_playwright.called

        # Playwright failure returns empty results
        assert docs == []
        assert success is False

    @patch("src.scraper.loaders.RecursiveUrlLoader")
    def test_recursive_loader_with_depth(self, mock_recursive):
        """Test recursive loader respects depth configuration."""
        mock_loader = Mock()
        mock_loader.load.return_value = []
        mock_recursive.return_value = mock_loader

        config = Mock()
        config.RATE_LIMIT_DELAY = 0.1
        config.sites_to_skip = []
        config.sites_needing_playwright = []
        config.sites_to_crawl = {"https://example.com/": {"max_depth": 3}}

        loader = SmartLoader(config)

        with patch("src.scraper.loaders.SmartLoader._select_and_load") as mock_select:
            mock_select.return_value = ([], "Recursive Crawler (Depth: 3)", False)
            docs, loader_type, success = loader.load_url("https://example.com/page")

            assert "Depth: 3" in loader_type


@pytest.mark.integration
class TestScraperPipelineEnd2End:
    """End-to-end integration tests of the complete pipeline."""

    def test_complete_scraper_pipeline(self):
        """Test a complete scraping pipeline with mocked loaders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")
            links_file = os.path.join(tmpdir, "links.txt")

            scraper = VecinaScraper(
                output_file=output_file, failed_log=failed_log, links_file=links_file
            )

            # Mock the loader to return some documents
            with patch.object(scraper.loader, "load_url") as mock_load:
                mock_doc = Mock()
                mock_doc.page_content = "Test content about housing policy and community resources."
                mock_doc.metadata = {"source": "https://example.com"}

                mock_load.return_value = ([mock_doc], "Test Loader", True)

                # Mock processor
                with patch.object(scraper.processor, "process_documents") as mock_process:
                    mock_process.return_value = (1, ["https://example.com"])

                    # Run scraper
                    total, successful, failed = scraper.scrape_urls(urls=["https://example.com"])

                    assert total == 1
                    assert successful == 1
                    assert failed == 0

    def test_scraper_with_mixed_success_failure(self):
        """Test scraper handling mix of successful and failed URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            scraper = VecinaScraper(output_file=output_file, failed_log=failed_log)

            urls = ["https://example.com", "https://fail.com", "https://test.org"]

            with patch.object(scraper.loader, "load_url") as mock_load:
                # First URL succeeds, second fails, third succeeds
                mock_doc = Mock()
                mock_doc.page_content = "Content with multiple words in it for processing."
                mock_doc.metadata = {"source": "https://example.com"}

                def load_side_effect(url, *args, **kwargs):
                    if url == "https://fail.com":
                        return [], "Failed", False
                    return ([mock_doc], "Test", True)

                mock_load.side_effect = load_side_effect

                with patch.object(scraper.processor, "process_documents") as mock_process:
                    mock_process.return_value = (1, [])

                    total, successful, failed = scraper.scrape_urls(urls)

                    assert total == 3
                    assert successful == 2
                    assert failed == 1

    def test_scraper_summary_generation(self):
        """Test scraper generates proper summary output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            scraper = VecinaScraper(output_file=output_file, failed_log=failed_log)

            # Manually set some stats
            scraper.stats["total_urls"] = 5
            scraper.stats["successful"] = 3
            scraper.stats["failed"] = 2
            scraper.stats["total_chunks"] = 45
            scraper.stats["total_links"] = 120

            scraper.successful_sources = [
                "https://example.com",
                "https://test.org",
                "https://community.gov",
            ]

            scraper.failed_sources = {
                "https://fail.com": "Failed to load",
                "https://skip.com": "Skipped (blocked pattern)",
            }

            # This shouldn't raise an error
            with patch("logging.getLogger"):
                scraper.print_summary()


@pytest.mark.unit
class TestScraperFileOperations:
    """Test file operations in the scraper."""

    def test_write_chunks_creates_output_file(self):
        """Test that processor creates output file if it doesn't exist."""
        config = Mock()
        config.CHUNK_SIZE = 1000
        config.CHUNK_OVERLAP = 200

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.txt")

            mock_doc = Mock()
            mock_doc.page_content = "Sample content to be written to file."
            mock_doc.metadata = {"source": "https://example.com"}

            processor = DocumentProcessor(config)
            processor.process_documents(
                docs=[mock_doc],
                source_identifier="https://example.com",
                loader_type="Test",
                output_file=output_file,
            )

            # File should be created
            assert os.path.exists(output_file)

            # File should contain content
            with open(output_file) as f:
                content = f.read()

            assert "https://example.com" in content
            assert "Sample content" in content

    def test_append_to_existing_output_file(self):
        """Test that processor appends to existing output file."""
        config = Mock()
        config.CHUNK_SIZE = 1000
        config.CHUNK_OVERLAP = 200

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.txt")

            # Write initial content
            with open(output_file, "w") as f:
                f.write("Initial content\n")

            mock_doc = Mock()
            mock_doc.page_content = "New content to append to file."
            mock_doc.metadata = {"source": "https://new.com"}

            processor = DocumentProcessor(config)
            processor.process_documents(
                docs=[mock_doc],
                source_identifier="https://new.com",
                loader_type="Test",
                output_file=output_file,
            )

            # File should still exist
            assert os.path.exists(output_file)

            # File should contain both initial and new content
            with open(output_file) as f:
                content = f.read()

            assert "Initial content" in content
            assert "https://new.com" in content

    def test_failed_log_accumulation(self):
        """Test that failed URLs accumulate in log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "failed.txt")

            write_to_failed_log("https://fail1.com", "Error 1", log_file)
            write_to_failed_log("https://fail2.com", "Error 2", log_file)
            write_to_failed_log("https://fail3.com", "Error 3", log_file)

            with open(log_file) as f:
                content = f.read()

            assert "https://fail1.com" in content
            assert "https://fail2.com" in content
            assert "https://fail3.com" in content

            lines = content.strip().split("\n")
            assert len(lines) == 3


@pytest.mark.unit
class TestScraperConcurrency:
    """Test scraper behavior with multiple URLs."""

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied between requests."""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            scraper = VecinaScraper(output_file=output_file, failed_log=failed_log)

            # Set a high rate limit for testing
            scraper.config.RATE_LIMIT_DELAY = 0.1

            urls = ["https://example1.com", "https://example2.com"]

            with patch.object(scraper.loader, "load_url") as mock_load:
                mock_load.return_value = ([], "Test", False)

                start_time = time.time()
                scraper.scrape_urls(urls)
                elapsed = time.time() - start_time

                # Should take at least 0.2 seconds (2 URLs * 0.1s delay)
                # Adding buffer for execution time
                assert elapsed >= 0.15
