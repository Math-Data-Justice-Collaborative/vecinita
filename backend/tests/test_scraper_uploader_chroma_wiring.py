"""Unit tests for scraper uploader wiring to Chroma-backed implementation."""

import pytest

pytestmark = pytest.mark.unit


def test_scraper_uploader_reexports_services_chroma_uploader():
    from src.scraper.uploader import DatabaseUploader as CliUploader
    from src.services.scraper.uploader import DatabaseUploader as ServicesUploader

    assert CliUploader is ServicesUploader


def test_scraper_uploader_reexports_document_chunk_dataclass():
    from src.scraper.uploader import DocumentChunk as CliChunk
    from src.services.scraper.uploader import DocumentChunk as ServicesChunk

    assert CliChunk is ServicesChunk
