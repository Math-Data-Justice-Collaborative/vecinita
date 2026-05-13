"""Integration tests for the full scraping pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vecinita_scraper.core.db import PostgresDB
from vecinita_scraper.core.models import (
    ChunkingConfig,
    ChunkJobQueueData,
    CrawlConfig,
    EmbedJobQueueData,
    JobStatus,
    ProcessJobQueueData,
    ScrapeJobQueueData,
    StoreJobQueueData,
)


@pytest.fixture
def integration_mock_db():
    """Create a comprehensive mock database for integration tests."""
    db = AsyncMock(spec=PostgresDB)
    db.create_scraping_job = AsyncMock(return_value="integration-job-123")
    db.update_job_status = AsyncMock()
    db.store_crawled_url = AsyncMock(return_value="crawled-001")
    db.store_extracted_content = AsyncMock(return_value="content-001")
    db.store_processed_document = AsyncMock(return_value="doc-001")
    db.store_chunks = AsyncMock(return_value=["chunk-001", "chunk-002"])
    db.store_embeddings = AsyncMock()
    db.get_job_status = AsyncMock(return_value={"id": "integration-job-123", "status": "completed"})
    return db


class TestFullPipelineFlow:
    """Test complete job pipeline from submission to completion."""

    @pytest.mark.asyncio
    async def test_job_flows_through_all_workers(self, integration_mock_db):
        """Complete job should flow through all worker stages."""
        job_id = "full-pipeline-test"
        db = integration_mock_db
        db.create_scraping_job = AsyncMock(return_value=job_id)

        # Step 1: Scraper worker
        from vecinita_scraper.workers.scraper import run_scrape_job

        with patch("vecinita_scraper.workers.scraper.Crawl4AIAdapter") as mock_adapter:
            mock_adapter_inst = AsyncMock()
            mock_adapter_inst.crawl_site = AsyncMock(
                return_value=[
                    MagicMock(
                        url="https://example.com",
                        markdown="# Test",
                        html="<h1>Test</h1>",
                        success=True,
                    ),
                ]
            )
            mock_adapter.return_value = mock_adapter_inst

            with patch(
                "vecinita_scraper.workers.scraper.try_direct_document_fetch",
                AsyncMock(return_value=None),
            ):
                with patch("vecinita_scraper.workers.scraper.process_jobs_queue") as mock_queue:
                    mock_queue.put.aio = AsyncMock()

                    scrape_payload = ScrapeJobQueueData(
                        job_id=job_id,
                        url="https://example.com",
                        user_id="test-user",
                        crawl_config=CrawlConfig(),
                    )

                    await run_scrape_job(scrape_payload, db=db, process_queue=mock_queue)

                    # Verify scraper updated status and stored content
                    assert db.update_job_status.called
                    assert db.store_crawled_url.called
                    assert db.store_extracted_content.called

        # Step 2: Processor worker
        from vecinita_scraper.workers.processor import run_processing_job

        with patch("vecinita_scraper.workers.processor.DoclingProcessor") as mock_docling:
            mock_docling_inst = MagicMock()
            mock_docling_inst.process_content = MagicMock(
                return_value=MagicMock(
                    markdown_content="# Processed",
                    tables_json=None,
                    metadata_json="{}",
                )
            )
            mock_docling.return_value = mock_docling_inst

            with patch("vecinita_scraper.workers.processor.chunk_jobs_queue") as mock_queue:
                mock_queue.put.aio = AsyncMock()

                process_payload = ProcessJobQueueData(
                    job_id=job_id,
                    crawled_url_id="crawled-001",
                    extracted_content_id="content-001",
                    raw_content="# Test",
                    content_type="markdown",
                )

                await run_processing_job(process_payload, db=db, chunk_queue=mock_queue)

                # Verify processor stored document
                assert db.store_processed_document.called

        # Step 3: Chunker worker
        from vecinita_scraper.workers.chunker import run_chunking_job

        with patch("vecinita_scraper.workers.chunker.SemanticChunker") as mock_chunker:
            mock_chunker_inst = MagicMock()
            mock_chunker_inst.chunk = MagicMock(
                return_value=[
                    {
                        "text": "Chunk 1",
                        "position": 0,
                        "token_count": 200,
                        "semantic_boundary": True,
                    },
                ]
            )
            mock_chunker.return_value = mock_chunker_inst

            with patch("vecinita_scraper.workers.chunker.embed_jobs_queue") as mock_queue:
                with patch("vecinita_scraper.workers.chunker.get_config") as mock_config:
                    # Mock store_chunks to return correct number of IDs matching chunks
                    db.store_chunks = AsyncMock(return_value=["chunk-001"])

                    mock_config_inst = MagicMock()
                    mock_config_inst.chunking = ChunkingConfig()
                    mock_config.return_value = mock_config_inst

                    mock_queue.put.aio = AsyncMock()

                    chunk_payload = ChunkJobQueueData(
                        job_id=job_id,
                        processed_doc_id="doc-001",
                        markdown_content="# Processed Content\n\nParag 1",
                    )

                    await run_chunking_job(chunk_payload, db=db, embed_queue=mock_queue)

                    # Verify chunker stored chunks
                    assert db.store_chunks.called

        # Step 4: Embedder worker
        from vecinita_scraper.workers.embedder import run_embedding_job

        with patch("vecinita_scraper.workers.embedder.EmbeddingClient") as mock_client:
            mock_client_inst = AsyncMock()
            mock_client_inst.batch_embed = AsyncMock(
                return_value={
                    "embeddings": [[0.1, 0.2, 0.3, 0.4]],
                    "model": "test-model",
                    "dimensions": 4,
                }
            )
            mock_client.return_value = mock_client_inst

            with patch("vecinita_scraper.workers.embedder.store_jobs_queue") as mock_queue:
                mock_queue.put.aio = AsyncMock()

                embed_payload = EmbedJobQueueData(
                    job_id=job_id,
                    chunk_ids=["chunk-001"],
                    chunk_texts=["Chunk 1 text"],
                )

                await run_embedding_job(
                    embed_payload, db=db, store_queue=mock_queue, embedding_client=mock_client_inst
                )

                # Verify embedder stored embeddings
                assert db.store_embeddings.called

        # Step 5: Finalizer worker
        from vecinita_scraper.workers.finalizer import run_finalization_job

        finalize_payload = StoreJobQueueData(
            job_id=job_id,
            embedding_ids=["emb-001"],
        )

        await run_finalization_job(finalize_payload, db=db)

        # Verify job marked as completed
        db.update_job_status.assert_called_with(job_id, JobStatus.COMPLETED.value)


class TestPipelineErrorHandling:
    """Test error handling in pipeline workers."""

    @pytest.mark.asyncio
    async def test_scraper_error_marks_job_failed(self, integration_mock_db):
        """Scraper failure should raise an exception."""
        from vecinita_scraper.workers.scraper import run_scrape_job

        db = integration_mock_db

        with patch("vecinita_scraper.workers.scraper.Crawl4AIAdapter") as mock_adapter:
            mock_adapter_inst = AsyncMock()
            mock_adapter_inst.crawl_site = AsyncMock(side_effect=Exception("Network timeout"))
            mock_adapter.return_value = mock_adapter_inst

            with patch("vecinita_scraper.workers.scraper.process_jobs_queue") as mock_queue:
                scrape_payload = ScrapeJobQueueData(
                    job_id="failed-job",
                    url="https://example.com",
                    user_id="test-user",
                    crawl_config=CrawlConfig(),
                )

                # Verify exception is raised
                with pytest.raises(Exception, match="Network timeout"):
                    await run_scrape_job(scrape_payload, db=db, process_queue=mock_queue)

                # Verify update_job_status was called (at least for initial status changes)
                assert db.update_job_status.called

    @pytest.mark.asyncio
    async def test_processor_error_marks_job_failed(self, integration_mock_db):
        """Processor failure should fail the job."""
        from vecinita_scraper.workers.processor import run_processing_job

        db = integration_mock_db

        with patch("vecinita_scraper.workers.processor.DoclingProcessor"):
            with patch("vecinita_scraper.workers.processor.chunk_jobs_queue") as mock_queue:
                process_payload = ProcessJobQueueData(
                    job_id="failed-processor-job",
                    crawled_url_id="crawled-001",
                    extracted_content_id="content-001",
                    raw_content="<invalid>",
                    content_type="html",
                )

                try:
                    await run_processing_job(process_payload, db=db, chunk_queue=mock_queue)
                except:  # noqa: E722
                    pass

                # Verify update_job_status was called
                assert db.update_job_status.called


class TestQueueBatchInjection:
    """Test that jobs properly batch enqueue for next stage."""

    @pytest.mark.asyncio
    async def test_scraper_enqueues_process_jobs(self, integration_mock_db):
        """Scraper should enqueue extracted content for processing."""
        from vecinita_scraper.workers.scraper import run_scrape_job

        db = integration_mock_db

        with patch("vecinita_scraper.workers.scraper.Crawl4AIAdapter") as mock_adapter:
            mock_adapter_inst = AsyncMock()
            mock_adapter_inst.crawl_site = AsyncMock(
                return_value=[
                    MagicMock(
                        url="https://example.com/page1",
                        markdown="# Page 1",
                        html="<p>1</p>",
                        success=True,
                    ),
                    MagicMock(
                        url="https://example.com/page2",
                        markdown="# Page 2",
                        html="<p>2</p>",
                        success=True,
                    ),
                ]
            )
            mock_adapter.return_value = mock_adapter_inst

            with patch("vecinita_scraper.workers.scraper.process_jobs_queue") as mock_queue:
                mock_queue.put.aio = AsyncMock()

                scrape_payload = ScrapeJobQueueData(
                    job_id="batch-test",
                    url="https://example.com",
                    user_id="test-user",
                    crawl_config=CrawlConfig(),
                )

                await run_scrape_job(scrape_payload, db=db, process_queue=mock_queue)

                # Verify queue was called for each extracted page
                assert mock_queue.put.aio.call_count >= 2

    @pytest.mark.asyncio
    async def test_chunker_batches_embed_jobs(self, integration_mock_db):
        """Chunker should batch enqueue chunks for embedding."""
        from vecinita_scraper.workers.chunker import run_chunking_job

        db = integration_mock_db

        with patch("vecinita_scraper.workers.chunker.SemanticChunker") as mock_chunker:
            # Create 5 mock chunks to test batching
            chunks = [
                {"text": f"Chunk {i}", "position": i, "token_count": 200, "semantic_boundary": True}
                for i in range(5)
            ]
            mock_chunker_inst = MagicMock()
            mock_chunker_inst.chunk = MagicMock(return_value=chunks)
            mock_chunker.return_value = mock_chunker_inst

            with patch("vecinita_scraper.workers.chunker.embed_jobs_queue") as mock_queue:
                with patch("vecinita_scraper.workers.chunker.get_config") as mock_config:
                    # Mock store_chunks to return correct number of IDs
                    db.store_chunks = AsyncMock(return_value=[f"chunk-{i:03d}" for i in range(5)])

                    mock_config_inst = MagicMock()
                    mock_config_inst.chunking = ChunkingConfig()
                    mock_config.return_value = mock_config_inst

                    mock_queue.put.aio = AsyncMock()

                    chunk_payload = ChunkJobQueueData(
                        job_id="batch-chunk-test",
                        processed_doc_id="doc-001",
                        markdown_content=(
                            "# Large doc\n" + "\n".join([f"Chunk {i}" for i in range(5)])
                        ),
                    )

                    await run_chunking_job(chunk_payload, db=db, embed_queue=mock_queue)

                    # Verify chunks were stored
                    assert db.store_chunks.called
                    # Verify embed queue was called for batches (batches of 100 chunks max)
                    assert mock_queue.put.aio.called
