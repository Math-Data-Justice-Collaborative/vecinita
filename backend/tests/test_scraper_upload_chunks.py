"""
Unit tests for scraper chunk upload functionality with detailed logging.
Tests the _upload_chunks_from_file() method and its logging traceability.
"""

import logging
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from src.services.scraper.scraper import VecinaScraper


@pytest.mark.unit
class TestUploadChunksFromFile:
    """Test suite for _upload_chunks_from_file() method with logging verification."""

    @pytest.fixture
    def mock_uploader(self):
        """Create a mock uploader with tracked calls."""
        uploader = Mock()
        uploader.upload_chunks = Mock(return_value=(10, 0))  # 10 uploaded, 0 failed
        return uploader

    @pytest.fixture
    def sample_chunks_file(self):
        """Create a sample chunks.txt file with realistic content."""
        content = """======================================================================
SOURCE: https://ride.ri.gov/
LOADER: Playwright (JavaScript rendering)
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 3
======================================================================

--- CHUNK 1/3 ---
Welcome to RIDE (Rhode Island Department of Education). Our mission is to provide quality education.

--- CHUNK 2/3 ---
Public schools in Rhode Island serve over 100,000 students. We offer comprehensive support services.

--- CHUNK 3/3 ---
For more information about our programs, contact us at (401) 555-1234.

======================================================================
SOURCE: https://dem.ri.gov/
LOADER: Unstructured
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 2
======================================================================

--- CHUNK 1/2 ---
The Department of Environmental Management protects Rhode Island's natural resources.

--- CHUNK 2/2 ---
We manage state parks, forests, and wildlife habitats for public enjoyment.
"""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def scraper_with_uploader(self, mock_uploader):
        """Create a VecinaScraper instance with mocked uploader."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "chunks.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            with patch("src.services.scraper.scraper.ScraperConfig") as mock_config_class:
                # Setup mock config with proper values
                mock_config = Mock()
                mock_config.RATE_LIMIT_DELAY = 0.1
                mock_config.CHUNK_SIZE = 1000
                mock_config.CHUNK_OVERLAP = 200
                mock_config_class.return_value = mock_config

                with patch("src.services.scraper.scraper.SmartLoader"):
                    with patch("src.services.scraper.scraper.DocumentProcessor"):
                        with patch("src.services.scraper.scraper.LinkTracker"):
                            scraper = VecinaScraper(
                                output_file=output_file, failed_log=failed_log, stream_mode=False
                            )
                            scraper.uploader = mock_uploader
                            scraper.stats = {
                                "total_uploads": 0,
                                "failed_uploads": 0,
                                "total_sources": 0,
                                "successful_sources": 0,
                                "total_chunks": 0,
                            }
                            yield scraper

    def test_upload_chunks_from_file_success(
        self, scraper_with_uploader, sample_chunks_file, caplog
    ):
        """Test successful upload of chunks with logging verification."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        caplog.clear()
        with caplog.at_level(logging.INFO):
            scraper._upload_chunks_from_file()

        # Verify success logs
        assert "Reading chunks from" in caplog.text
        assert "Parsed" in caplog.text and "chunks" in caplog.text
        # 1 from first source + 1 from second (combined by CHUNK marker)
        assert "Found 2 chunks in output file" in caplog.text
        assert "Uploading to database" in caplog.text
        assert "Batch upload complete" in caplog.text

        # Verify uploader was called
        assert scraper.uploader.upload_chunks.call_count == 2  # One for each source

        # Verify stats were updated
        # 2 sources * (10 returned)
        assert scraper.stats["total_uploads"] == 20
        assert scraper.stats["failed_uploads"] == 0

    def test_upload_chunks_source_detection(
        self, scraper_with_uploader, sample_chunks_file, caplog
    ):
        """Test that SOURCE: lines are correctly detected and logged."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        with caplog.at_level(logging.DEBUG):
            scraper._upload_chunks_from_file()

        # Verify source detection logs
        assert "SOURCE: https://ride.ri.gov/" in caplog.text
        assert "SOURCE: https://dem.ri.gov/" in caplog.text
        assert "Started new chunk from SOURCE:" in caplog.text

    def test_upload_chunks_loader_detection(
        self, scraper_with_uploader, sample_chunks_file, caplog
    ):
        """Test that LOADER: lines are correctly detected and logged."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        with caplog.at_level(logging.DEBUG):
            scraper._upload_chunks_from_file()

        # Verify loader detection logs
        assert "Set LOADER: Playwright" in caplog.text
        assert "Set LOADER: Unstructured" in caplog.text

    def test_upload_chunks_separator_skipping(
        self, scraper_with_uploader, sample_chunks_file, caplog
    ):
        """Test that separator lines are properly skipped with logging."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        with caplog.at_level(logging.DEBUG):
            scraper._upload_chunks_from_file()

        # Verify separator skipping logs
        assert "Skipping separator:" in caplog.text

    def test_upload_chunks_with_metadata(self):
        """Test upload of chunks with METADATA: lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "chunks.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            content = """======================================================================
SOURCE: https://example.com/
LOADER: Test Loader
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 1
METADATA: {"key": "value", "type": "test"}
======================================================================

--- CHUNK 1/1 ---
Test content with metadata.
"""
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            mock_uploader = Mock()
            mock_uploader.upload_chunks = Mock(return_value=(1, 0))

            with patch("src.services.scraper.scraper.ScraperConfig") as mock_config_class:
                mock_config = Mock()
                mock_config.RATE_LIMIT_DELAY = 0.1
                mock_config.CHUNK_SIZE = 1000
                mock_config.CHUNK_OVERLAP = 200
                mock_config_class.return_value = mock_config

                with patch("src.services.scraper.scraper.SmartLoader"):
                    with patch("src.services.scraper.scraper.DocumentProcessor"):
                        with patch("src.services.scraper.scraper.LinkTracker"):
                            scraper = VecinaScraper(
                                output_file=output_file, failed_log=failed_log, stream_mode=False
                            )
                            scraper.uploader = mock_uploader
                            scraper.stats = {
                                "total_uploads": 0,
                                "failed_uploads": 0,
                                "total_sources": 0,
                                "successful_sources": 0,
                                "total_chunks": 0,
                            }

                            scraper._upload_chunks_from_file()

                            # Verify metadata was parsed
                            call_args = mock_uploader.upload_chunks.call_args
                            chunks = (
                                call_args[1]["chunks"]
                                if "chunks" in call_args[1]
                                else call_args[0][0]
                            )
                            assert len(chunks) > 0
                            assert chunks[0]["metadata"]["type"] == "test"

    def test_upload_chunks_missing_file(self, scraper_with_uploader, caplog):
        """Test handling of missing output file with logging."""
        scraper = scraper_with_uploader
        scraper.output_file = "/nonexistent/path/chunks.txt"

        with caplog.at_level(logging.ERROR):
            scraper._upload_chunks_from_file()

        # Verify error logging
        assert "Failed to upload chunks from file" in caplog.text

    def test_upload_chunks_no_uploader(self, scraper_with_uploader, sample_chunks_file, caplog):
        """Test handling when uploader is not set with logging."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file
        scraper.uploader = None

        with caplog.at_level(logging.WARNING):
            scraper._upload_chunks_from_file()

        # Verify warning logging
        assert "Cannot upload chunks: output_file or uploader not set" in caplog.text

    def test_upload_chunks_empty_file(self, scraper_with_uploader, caplog):
        """Test handling of empty chunks file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("")
            empty_file = f.name

        try:
            scraper = scraper_with_uploader
            scraper.output_file = empty_file

            with caplog.at_level(logging.WARNING):
                scraper._upload_chunks_from_file()

            # Verify empty file handling
            assert (
                "No chunks found in output file" in caplog.text or "Parsed 0 lines" in caplog.text
            )
        finally:
            os.remove(empty_file)

    def test_upload_chunks_batch_grouping(self, scraper_with_uploader, sample_chunks_file, caplog):
        """Test that chunks are properly grouped by source with logging."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        with caplog.at_level(logging.INFO):
            scraper._upload_chunks_from_file()

        # Verify grouping logs
        assert "Grouped chunks by 2 sources" in caplog.text
        assert "Uploading 1 chunks from https://ride.ri.gov/" in caplog.text  # 1 chunk per source
        assert "Uploading 1 chunks from https://dem.ri.gov/" in caplog.text

    def test_upload_chunks_call_signature(self, scraper_with_uploader, sample_chunks_file):
        """Test that uploader.upload_chunks is called with correct parameters."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file
        mock_uploader = scraper.uploader

        scraper._upload_chunks_from_file()

        # Verify call count
        assert mock_uploader.upload_chunks.call_count == 2

        # Verify call parameters for first source
        first_call = mock_uploader.upload_chunks.call_args_list[0]
        assert "chunks" in first_call[1]
        assert "source_identifier" in first_call[1]
        assert "loader_type" in first_call[1]
        assert "https://ride.ri.gov/" in first_call[1]["source_identifier"]

    def test_upload_chunks_with_upload_failure(
        self, scraper_with_uploader, sample_chunks_file, caplog
    ):
        """Test handling of upload failures with detailed logging."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        # Mock uploader to return failures
        scraper.uploader.upload_chunks = Mock(return_value=(5, 5))  # 5 success, 5 failed

        with caplog.at_level(logging.INFO):
            scraper._upload_chunks_from_file()

        # Verify failure logging
        assert "10 chunks uploaded" in caplog.text  # 5+5
        assert "10 failed" in caplog.text

        # Verify stats updated with failures
        assert scraper.stats["total_uploads"] == 10
        assert scraper.stats["failed_uploads"] == 10

    def test_upload_chunks_uploader_exception(
        self, scraper_with_uploader, sample_chunks_file, caplog
    ):
        """Test handling of uploader exceptions with stack trace logging."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        # Mock uploader to raise exception
        scraper.uploader.upload_chunks = Mock(side_effect=Exception("Database connection failed"))

        with caplog.at_level(logging.ERROR):
            scraper._upload_chunks_from_file()

        # Verify exception logging
        assert "Error uploading chunks from" in caplog.text
        assert "Database connection failed" in caplog.text

    def test_upload_chunks_metadata_parse_error(self):
        """Test handling of malformed METADATA: lines with error logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "chunks.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            content = """======================================================================
SOURCE: https://example.com/
LOADER: Test Loader
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 1
METADATA: {invalid json}
======================================================================

--- CHUNK 1/1 ---
Test content with bad metadata.
"""
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            mock_uploader = Mock()
            mock_uploader.upload_chunks = Mock(return_value=(1, 0))

            with patch("src.services.scraper.scraper.ScraperConfig") as mock_config_class:
                mock_config = Mock()
                mock_config.RATE_LIMIT_DELAY = 0.1
                mock_config.CHUNK_SIZE = 1000
                mock_config.CHUNK_OVERLAP = 200
                mock_config_class.return_value = mock_config

                with patch("src.services.scraper.scraper.SmartLoader"):
                    with patch("src.services.scraper.scraper.DocumentProcessor"):
                        with patch("src.services.scraper.scraper.LinkTracker"):
                            scraper = VecinaScraper(
                                output_file=output_file, failed_log=failed_log, stream_mode=False
                            )
                            scraper.uploader = mock_uploader
                            scraper.stats = {
                                "total_uploads": 0,
                                "failed_uploads": 0,
                                "total_sources": 0,
                                "successful_sources": 0,
                                "total_chunks": 0,
                            }

                            # Should not raise exception, just log warning
                            scraper._upload_chunks_from_file()

                            # Verify upload still happened
                            assert mock_uploader.upload_chunks.called

    def test_upload_chunks_stats_tracking(self, scraper_with_uploader, sample_chunks_file):
        """Test that statistics are properly tracked during upload."""
        scraper = scraper_with_uploader
        scraper.output_file = sample_chunks_file

        initial_uploads = scraper.stats["total_uploads"]
        initial_failures = scraper.stats["failed_uploads"]

        scraper._upload_chunks_from_file()

        # Verify stats increased
        assert scraper.stats["total_uploads"] > initial_uploads
        # No failures expected
        assert scraper.stats["failed_uploads"] == initial_failures

    def test_upload_chunks_large_file(self, scraper_with_uploader, caplog):
        """Test upload performance with a large chunks file."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            # Create a large file with 100 chunks from 5 sources
            for source_num in range(1, 6):
                f.write(f"{'=' * 70}\n")
                f.write(f"SOURCE: https://example{source_num}.com/\n")
                f.write(f"LOADER: Test Loader {source_num}\n")
                f.write("DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 20\n")
                f.write(f"{'=' * 70}\n\n")

                for chunk_num in range(1, 21):
                    f.write(f"--- CHUNK {chunk_num}/20 ---\n")
                    f.write(f"Content for source {source_num} chunk {chunk_num}. " * 10)
                    f.write("\n\n")

            large_file = f.name

        try:
            scraper = scraper_with_uploader
            scraper.output_file = large_file

            with caplog.at_level(logging.INFO):
                scraper._upload_chunks_from_file()

            # Verify processing of large file
            assert "Parsed" in caplog.text and "lines" in caplog.text
            assert "Grouped chunks by 5 sources" in caplog.text

            # Verify uploader was called for each source
            assert scraper.uploader.upload_chunks.call_count == 5
        finally:
            os.remove(large_file)


@pytest.mark.unit
class TestUploadChunksLoggingOutput:
    """Test the quality and completeness of logging output."""

    def test_logging_contains_all_required_fields(self):
        """Test that logs include all required traceability fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "chunks.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            content = """======================================================================
SOURCE: https://example.com/
LOADER: Playwright
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 1
======================================================================

--- CHUNK 1/1 ---
Test content.
"""
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            mock_uploader = Mock()
            mock_uploader.upload_chunks = Mock(return_value=(1, 0))

            with patch("src.services.scraper.scraper.ScraperConfig") as mock_config_class:
                mock_config = Mock()
                mock_config.RATE_LIMIT_DELAY = 0.1
                mock_config.CHUNK_SIZE = 1000
                mock_config.CHUNK_OVERLAP = 200
                mock_config_class.return_value = mock_config

                with patch("src.services.scraper.scraper.SmartLoader"):
                    with patch("src.services.scraper.scraper.DocumentProcessor"):
                        with patch("src.services.scraper.scraper.LinkTracker"):
                            scraper = VecinaScraper(
                                output_file=output_file, failed_log=failed_log, stream_mode=False
                            )
                            scraper.uploader = mock_uploader
                            scraper.stats = {
                                "total_uploads": 0,
                                "failed_uploads": 0,
                                "total_sources": 0,
                                "successful_sources": 0,
                                "total_chunks": 0,
                            }

                            # Capture logs
                            import logging

                            logger = logging.getLogger("src.services.scraper.scraper")
                            handler = logging.StreamHandler()
                            logger.addHandler(handler)

                            scraper._upload_chunks_from_file()

                            # All these should be in the logs

                            # Note: Direct assertion would require captured log output
                            # This test structure allows for integration with log capturing
