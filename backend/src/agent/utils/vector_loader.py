#!/usr/bin/env python3
# vector_loader.py
"""
Vecinita Data Loader
Loads scraped content chunks into Supabase vector database with embeddings
Supports source attribution and batch processing for large files
"""

import json
import logging
import os
import re
import sys
import time
import uuid
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, cast

from dotenv import load_dotenv
from supabase import Client, create_client
from tqdm import tqdm  # type: ignore[import-untyped]

try:
    import psycopg2

    POSTGRES_AVAILABLE = True
except Exception:
    psycopg2 = None  # type: ignore[assignment]
    POSTGRES_AVAILABLE = False

# Optional: For local embeddings (install: pip install sentence-transformers)
try:
    from sentence_transformers import SentenceTransformer

    LOCAL_EMBEDDINGS_AVAILABLE = True
except ImportError:
    LOCAL_EMBEDDINGS_AVAILABLE = False
    print(
        "Warning: sentence-transformers not installed. Install with: pip install sentence-transformers"
    )

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("vecinita_loader.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 100  # Number of chunks to process in one batch
LOCAL_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
USE_LOCAL_EMBEDDINGS = os.getenv("USE_LOCAL_EMBEDDINGS", "true").lower() == "true"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


@dataclass
class DocumentChunk:
    """Represents a single document chunk with metadata"""

    content: str
    source_url: str
    chunk_index: int
    total_chunks: int | None = None
    document_id: str | None = None
    scraped_at: datetime | None = None
    metadata: dict | None = None


class VecinitaLoader:
    """Main class for loading data into Vecinita vector database"""

    def __init__(self):
        """Initialize the loader with database connection and embedding model"""
        self.db_data_mode = os.environ.get("DB_DATA_MODE", "auto").strip().lower()
        self.database_url = (os.environ.get("DATABASE_URL") or "").strip()

        use_postgres = self.db_data_mode == "postgres" and bool(self.database_url)
        self.use_postgres = use_postgres and POSTGRES_AVAILABLE
        if use_postgres and not POSTGRES_AVAILABLE:
            raise ValueError("DB_DATA_MODE=postgres requires psycopg2 to be installed")

        # Initialize Supabase client for legacy mode
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.supabase: Client | None = None

        if self.use_postgres:
            logger.info("Using direct Postgres mode for vector writes")
        else:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set unless DB_DATA_MODE=postgres"
                )
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info(f"Connected to Supabase at {self.supabase_url[:25]}...")

        # Initialize embedding model
        if USE_LOCAL_EMBEDDINGS:
            if LOCAL_EMBEDDINGS_AVAILABLE:
                self.embedding_model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
                self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
                logger.info(f"Using local embedding model: {LOCAL_EMBEDDING_MODEL}")
            else:
                # Respect config: don't hard-fail, proceed without embeddings
                logger.warning(
                    "USE_LOCAL_EMBEDDINGS=true but sentence-transformers not installed. Proceeding without embeddings."
                )
                self.embedding_model = None
                self.embedding_dimension = EMBEDDING_DIMENSION
        else:
            logger.warning("Local embeddings are disabled. Proceeding without embeddings.")
            self.embedding_model = None
            self.embedding_dimension = EMBEDDING_DIMENSION

    # --- THIS FUNCTION HAS BEEN REPLACED ---
    def parse_chunk_file(self, file_path: str) -> Generator[DocumentChunk, None, None]:
        """
        Parse a file containing scraped content chunks

        New format (Oct 2025):
        ======================================================================
        SOURCE: url
        ...
        ======================================================================
        --- CHUNK n/total ---
        content...
        --- CHUNK n+1/total ---
        content...
        """
        pattern_source = re.compile(r"SOURCE: (.+)")
        pattern_chunk_start = re.compile(r"--- CHUNK (\d+)/(\d+) ---")

        with open(file_path, encoding="utf-8") as f:
            current_source_url = None
            current_chunk = None
            content_lines: list[str] = []
            line_count = 0

            for line in f:
                line_count += 1
                line = line.strip()

                # Check for new source
                source_match = pattern_source.search(line)
                if source_match:
                    # Save previous chunk if exists (in case there's no chunk after a source)
                    if current_chunk and content_lines:
                        current_chunk.content = "\n".join(content_lines).strip()
                        if current_chunk.content:
                            yield current_chunk

                    current_source_url = source_match.group(1).strip()
                    logger.info(f"Found source: {current_source_url}")
                    current_chunk = None
                    content_lines = []
                    continue

                # Check for chunk start
                chunk_start_match = pattern_chunk_start.match(line)
                if chunk_start_match:
                    # Save previous chunk if exists
                    if current_chunk and content_lines:
                        current_chunk.content = "\n".join(content_lines).strip()
                        if current_chunk.content:  # Only yield non-empty chunks
                            yield current_chunk

                    # Start new chunk
                    if not current_source_url:
                        logger.warning(
                            f"Found chunk at line {line_count} but no source URL was set. Skipping."
                        )
                        current_chunk = None
                        content_lines = []  # reset content
                        continue

                    chunk_index = int(chunk_start_match.group(1))
                    total_chunks = int(chunk_start_match.group(2))

                    current_chunk = DocumentChunk(
                        content="",
                        source_url=current_source_url,
                        chunk_index=chunk_index,
                        total_chunks=total_chunks,
                        document_id=str(uuid.uuid4()),  # Generate document ID
                        scraped_at=datetime.now(timezone.utc),
                    )
                    content_lines = []
                    continue

                # Accumulate content lines
                if current_chunk is not None:
                    # Ignore empty lines between header and content
                    if line or content_lines:
                        content_lines.append(line)

            # Handle last chunk
            if current_chunk and content_lines:
                current_chunk.content = "\n".join(content_lines).strip()
                if current_chunk.content:
                    yield current_chunk

        logger.info(f"Parsed {line_count} lines from {file_path}")

    # --- END OF REPLACED FUNCTION ---

    def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for text using configured model"""
        if not text:
            return None

        try:
            if USE_LOCAL_EMBEDDINGS and hasattr(self, "embedding_model"):
                # Use local sentence transformer
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                return cast(list[float], embedding.tolist())
            else:
                return None
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def process_batch(self, chunks: list[DocumentChunk]) -> tuple[int, int]:
        """
        Process a batch of chunks: generate embeddings and insert into database
        Returns: (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        # Prepare batch data
        batch_data = []
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = self.generate_embedding(chunk.content)

                # Prepare record
                record = {
                    "content": chunk.content,
                    "source_url": chunk.source_url,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "document_id": chunk.document_id,
                    "scraped_at": chunk.scraped_at.isoformat() if chunk.scraped_at else None,
                    "is_processed": embedding is not None,
                    "processing_status": "completed" if embedding else "no_embedding",
                    "metadata": chunk.metadata or {},
                }

                # Add embedding if available
                if embedding:
                    record["embedding"] = embedding

                batch_data.append(record)

            except Exception as e:
                logger.error(f"Error preparing chunk {chunk.chunk_index}: {e}")
                failed += 1
                continue

        # Insert batch into database
        if batch_data:
            for attempt in range(MAX_RETRIES):
                try:
                    if self.use_postgres:
                        self._upsert_postgres_chunks(batch_data)
                    else:
                        if self.supabase is None:
                            raise RuntimeError("Supabase client is not initialized")
                        self.supabase.table("document_chunks").upsert(
                            batch_data  # type: ignore[arg-type]
                        ).execute()

                    successful = len(batch_data)
                    logger.info(f"Inserted batch of {successful} chunks")
                    break

                except Exception as e:
                    logger.error(f"Database insert error (attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        failed += len(batch_data)

        return successful, failed

    def create_chunks_from_content(
        self, content_list: list[tuple[str, dict]], source_url: str
    ) -> list[DocumentChunk]:
        """
        Create DocumentChunk objects from a list of (content, metadata) tuples.
        Used for streaming uploads directly from scraper without file I/O.

        Args:
            content_list: List of (content_text, metadata_dict) tuples
            source_url: Original source URL for attribution

        Returns:
            List of DocumentChunk objects ready for upload
        """
        chunks = []
        total_chunks = len(content_list)
        document_id = str(uuid.uuid4())
        scraped_at = datetime.now(timezone.utc)

        for idx, (content, metadata) in enumerate(content_list, start=1):
            chunk = DocumentChunk(
                content=content,
                # Use provided URL, not metadata['source']
                source_url=source_url,
                chunk_index=idx,
                total_chunks=total_chunks,
                document_id=document_id,
                scraped_at=scraped_at,
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks

    def load_chunks_directly(
        self, chunks: list[DocumentChunk], batch_size: int = BATCH_SIZE
    ) -> dict[str, int]:
        """
        Load DocumentChunk objects directly into database without file I/O.
        This enables streaming mode where scraper uploads immediately after processing.

        Args:
            chunks: List of DocumentChunk objects to upload
            batch_size: Number of chunks to process per batch

        Returns:
            Statistics dict with keys: total_chunks, successful, failed
        """
        stats = {"total_chunks": len(chunks), "successful": 0, "failed": 0, "skipped": 0}

        if not chunks:
            logger.warning("No chunks provided to load_chunks_directly()")
            return stats

        # Log the source being processed
        source_url = chunks[0].source_url if chunks else "unknown"
        logger.info(f"Streaming upload for source: {source_url} ({len(chunks)} chunks)")

        # Process chunks in batches
        batch = []
        for chunk in chunks:
            batch.append(chunk)

            if len(batch) >= batch_size:
                success, failed = self.process_batch(batch)
                stats["successful"] += success
                stats["failed"] += failed
                batch = []

        # Process remaining chunks
        if batch:
            success, failed = self.process_batch(batch)
            stats["successful"] += success
            stats["failed"] += failed

        logger.info(
            f"Streaming upload complete: {stats['successful']}/{stats['total_chunks']} chunks uploaded"
        )
        return stats

    def load_file(self, file_path: str, batch_size: int = BATCH_SIZE) -> dict[str, int]:
        """
        Load a single file into the database
        Returns statistics about the loading process
        """
        logger.info(f"Starting to load file: {file_path}")

        # Track statistics
        stats = {"total_chunks": 0, "successful": 0, "failed": 0, "skipped": 0}

        # Create processing queue entry
        queue_entry = {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "status": "processing",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        queue_id: str | None = None
        if self.use_postgres:
            queue_id = self._insert_processing_queue_postgres(queue_entry)
        else:
            if self.supabase is None:
                raise RuntimeError("Supabase client is not initialized")
            queue_response = self.supabase.table("processing_queue").insert(queue_entry).execute()  # type: ignore[arg-type]
            queue_data: list[dict[str, Any]] = queue_response.data or []  # type: ignore[assignment]
            queue_id = queue_data[0].get("id") if queue_data else None

        # Process chunks in batches
        batch = []

        try:
            # Create progress bar
            pbar = tqdm(desc="Processing chunks", unit="chunks")

            for chunk in self.parse_chunk_file(file_path):
                batch.append(chunk)
                stats["total_chunks"] += 1

                if len(batch) >= batch_size:
                    success, failed = self.process_batch(batch)
                    stats["successful"] += success
                    stats["failed"] += failed
                    pbar.update(len(batch))

                    # Update queue progress
                    if queue_id:
                        self._update_processing_queue_progress(queue_id, stats)

                    batch = []

            # Process remaining chunks
            if batch:
                success, failed = self.process_batch(batch)
                stats["successful"] += success
                stats["failed"] += failed
                pbar.update(len(batch))

            pbar.close()

            # Update queue as completed
            if queue_id:
                self._mark_processing_queue_complete(queue_id, stats)

        except Exception as e:
            logger.error(f"Error loading file: {e}")

            # Update queue as failed
            if queue_id:
                self._mark_processing_queue_failed(queue_id, str(e))

            raise

        logger.info(f"Completed loading {file_path}")
        logger.info(f"Statistics: {stats}")

        return stats

    def load_directory(
        self, directory_path: str, pattern: str = "*.txt"
    ) -> dict[str, dict[str, Any]]:
        """
        Load all matching files from a directory
        Returns statistics for each file
        """
        import glob

        all_stats: dict[str, dict[str, Any]] = {}
        file_pattern = os.path.join(directory_path, pattern)
        files = glob.glob(file_pattern)

        logger.info(f"Found {len(files)} files matching {pattern} in {directory_path}")

        for file_path in files:
            try:
                stats = self.load_file(file_path)
                all_stats[file_path] = stats
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
                all_stats[file_path] = {"error": str(e)}

        return all_stats

    def verify_installation(self) -> bool:
        """Verify that the database schema is properly installed"""
        try:
            if self.use_postgres:
                self._verify_postgres_tables()
            else:
                if self.supabase is None:
                    raise RuntimeError("Supabase client is not initialized")
                self.supabase.table("document_chunks").select("id").limit(1).execute()
            logger.info("✅ Database schema verified")
            return True
        except Exception as e:
            logger.error(f"❌ Database schema not found: {e}")
            logger.info("Please run the SQL schema file first to create the tables")
            return False

    def _vector_literal(self, embedding: Any) -> str | None:
        if not isinstance(embedding, list) or not embedding:
            return None
        return "[" + ",".join(f"{float(v):.10f}" for v in embedding) + "]"

    def _upsert_postgres_chunks(self, rows: list[dict[str, Any]]) -> None:
        if not self.database_url or psycopg2 is None:
            raise RuntimeError("Postgres mode is enabled but DATABASE_URL/psycopg2 is unavailable")

        sql = (
            "INSERT INTO document_chunks ("
            "content, source_url, chunk_index, total_chunks, document_id, document_title, "
            "scraped_at, metadata, is_processed, processing_status, embedding, updated_at"
            ") VALUES ("
            "%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::vector, TIMEZONE('utc', NOW())"
            ") "
            "ON CONFLICT ON CONSTRAINT unique_content_source DO UPDATE SET "
            "total_chunks = EXCLUDED.total_chunks, "
            "document_id = COALESCE(EXCLUDED.document_id, document_chunks.document_id), "
            "document_title = COALESCE(EXCLUDED.document_title, document_chunks.document_title), "
            "scraped_at = COALESCE(EXCLUDED.scraped_at, document_chunks.scraped_at), "
            "metadata = COALESCE(document_chunks.metadata, '{}'::jsonb) || COALESCE(EXCLUDED.metadata, '{}'::jsonb), "
            "is_processed = EXCLUDED.is_processed, "
            "processing_status = EXCLUDED.processing_status, "
            "embedding = COALESCE(EXCLUDED.embedding, document_chunks.embedding), "
            "updated_at = TIMEZONE('utc', NOW())"
        )

        with psycopg2.connect(self.database_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                for row in rows:
                    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
                    cur.execute(
                        sql,
                        (
                            row.get("content") or "",
                            row.get("source_url") or "",
                            int(row.get("chunk_index") or 0),
                            int(row.get("total_chunks") or 0),
                            row.get("document_id"),
                            row.get("document_title"),
                            row.get("scraped_at"),
                            json.dumps(metadata),
                            bool(row.get("is_processed", False)),
                            row.get("processing_status") or "pending",
                            self._vector_literal(row.get("embedding")),
                        ),
                    )

    def _insert_processing_queue_postgres(self, queue_entry: dict[str, Any]) -> str | None:
        if not self.database_url or psycopg2 is None:
            return None
        sql = (
            "INSERT INTO processing_queue (file_path, file_size, status, started_at) "
            "VALUES (%s, %s, %s, %s) RETURNING id"
        )
        with psycopg2.connect(self.database_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        queue_entry.get("file_path"),
                        queue_entry.get("file_size"),
                        queue_entry.get("status") or "processing",
                        queue_entry.get("started_at"),
                    ),
                )
                row = cur.fetchone()
                return str(row[0]) if row else None

    def _update_processing_queue_progress(self, queue_id: str, stats: dict[str, int]) -> None:
        if self.use_postgres:
            if not self.database_url or psycopg2 is None:
                return
            sql = (
                "UPDATE processing_queue SET chunks_processed = %s, total_chunks = %s WHERE id = %s"
            )
            with psycopg2.connect(self.database_url, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (stats["successful"], stats["total_chunks"], queue_id))
            return

        if self.supabase is not None:
            self.supabase.table("processing_queue").update(
                {
                    "chunks_processed": stats["successful"],
                    "total_chunks": stats["total_chunks"],
                }
            ).eq("id", queue_id).execute()

    def _mark_processing_queue_complete(self, queue_id: str, stats: dict[str, int]) -> None:
        payload = {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "chunks_processed": stats["successful"],
            "total_chunks": stats["total_chunks"],
        }
        if self.use_postgres:
            if not self.database_url or psycopg2 is None:
                return
            sql = "UPDATE processing_queue SET status = %s, completed_at = %s, chunks_processed = %s, total_chunks = %s WHERE id = %s"
            with psycopg2.connect(self.database_url, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql,
                        (
                            payload["status"],
                            payload["completed_at"],
                            payload["chunks_processed"],
                            payload["total_chunks"],
                            queue_id,
                        ),
                    )
            return

        if self.supabase is not None:
            self.supabase.table("processing_queue").update(payload).eq("id", queue_id).execute()

    def _mark_processing_queue_failed(self, queue_id: str, error_message: str) -> None:
        payload = {
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.use_postgres:
            if not self.database_url or psycopg2 is None:
                return
            sql = "UPDATE processing_queue SET status = %s, error_message = %s, completed_at = %s WHERE id = %s"
            with psycopg2.connect(self.database_url, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql,
                        (
                            payload["status"],
                            payload["error_message"],
                            payload["completed_at"],
                            queue_id,
                        ),
                    )
            return

        if self.supabase is not None:
            self.supabase.table("processing_queue").update(payload).eq("id", queue_id).execute()

    def _verify_postgres_tables(self) -> None:
        if not self.database_url or psycopg2 is None:
            raise RuntimeError("Postgres mode is enabled but DATABASE_URL/psycopg2 is unavailable")

        sql = (
            "SELECT to_regclass('public.document_chunks') AS document_chunks, "
            "to_regclass('public.processing_queue') AS processing_queue"
        )
        with psycopg2.connect(self.database_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
                if not row or not row[0]:
                    raise RuntimeError("document_chunks table is missing")


def main():
    """Main function to run the loader"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Load scraped content into Vecinita vector database"
    )
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE, help="Batch size for processing"
    )
    parser.add_argument("--pattern", default="*.txt", help="File pattern for directory loading")
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify database installation"
    )

    args = parser.parse_args()

    # Initialize loader
    loader = VecinitaLoader()

    # Verify installation
    if args.verify_only or not loader.verify_installation():
        if args.verify_only:
            sys.exit(0 if loader.verify_installation() else 1)
        else:
            sys.exit(1)

    # Load data
    if os.path.isfile(args.input):
        stats = loader.load_file(args.input, args.batch_size)
        print(f"\nLoading complete. Statistics: {stats}")
    elif os.path.isdir(args.input):
        all_stats = loader.load_directory(args.input, args.pattern)
        print(f"\nLoading complete. Processed {len(all_stats)} files")

        # Print summary
        total_successful = sum(
            s.get("successful", 0) for s in all_stats.values() if "successful" in s
        )
        total_failed = sum(s.get("failed", 0) for s in all_stats.values() if "failed" in s)
        print(f"Total chunks loaded: {total_successful}")
        print(f"Total chunks failed: {total_failed}")
    else:
        logger.error(f"Input path does not exist: {args.input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
# end-of-file--
