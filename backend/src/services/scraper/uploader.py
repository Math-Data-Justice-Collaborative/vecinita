"""
Database uploader for the VECINA scraper.
Handles uploading processed document chunks to Supabase vector database.
"""

import logging
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Import embedding service client (preferred)
try:
    from src.services.embedding.client import create_embedding_client
    EMBEDDING_SERVICE_AVAILABLE = True
except ImportError:
    EMBEDDING_SERVICE_AVAILABLE = False

# Import fallback embedding options
try:
    from langchain_community.embeddings import FastEmbedEmbeddings, HuggingFaceEmbeddings
    FALLBACK_EMBEDDINGS_AVAILABLE = True
except ImportError:
    FALLBACK_EMBEDDINGS_AVAILABLE = False

log = logging.getLogger('vecinita_pipeline.uploader')
log.addHandler(logging.NullHandler())


@dataclass
class DocumentChunk:
    """Represents a single document chunk with metadata."""
    content: str
    source_url: str
    chunk_index: int
    total_chunks: Optional[int] = None
    loader_type: Optional[str] = None
    metadata: Optional[Dict] = None
    scraped_at: Optional[datetime] = None


class DatabaseUploader:
    """Uploads processed chunks to Supabase vector database."""

    def __init__(self, use_local_embeddings: bool = True):
        """
        Initialize database uploader.

        Args:
            use_local_embeddings: If True, use embedding service (or fallback). If False, requires OpenAI API key.
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase client not installed. Install with: pip install supabase")

        self.use_local_embeddings = use_local_embeddings
        self.embedding_model = None
        self.embedding_client_type = None
        self.supabase_client = None

        # Initialize embeddings with fallback chain
        if use_local_embeddings:
            self._init_embeddings()

        # Initialize Supabase connection
        self._init_supabase()

    def _init_embeddings(self) -> None:
        """Initialize embedding model with fallback chain: Service → FastEmbed → HuggingFace."""
        # Try embedding service first (lightweight, scalable)
        embedding_service_url = os.getenv(
            "EMBEDDING_SERVICE_URL", "http://embedding-service:8001")

        if EMBEDDING_SERVICE_AVAILABLE:
            try:
                log.info(
                    f"Initializing Embedding Service client ({embedding_service_url})...")
                self.embedding_model = create_embedding_client(
                    embedding_service_url)
                self.embedding_client_type = "embedding_service"
                log.info(
                    f"✓ Embedding Service client initialized (384 dimensions)")
                return
            except Exception as e:
                log.warning(f"Embedding Service initialization failed: {e}")

        # Fallback to FastEmbed
        if FALLBACK_EMBEDDINGS_AVAILABLE:
            try:
                log.info("Falling back to FastEmbed (local)...")
                self.embedding_model = FastEmbedEmbeddings(
                    model_name="fast-bge-small-en-v1.5")
                self.embedding_client_type = "fastembed"
                log.info("✓ FastEmbed initialized (384 dimensions)")
                return
            except Exception as e:
                log.warning(f"FastEmbed initialization failed: {e}")

        # Final fallback to HuggingFace
        if FALLBACK_EMBEDDINGS_AVAILABLE:
            try:
                log.info("Falling back to HuggingFace (local)...")
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                self.embedding_client_type = "huggingface"
                log.info("✓ HuggingFace embeddings initialized (384 dimensions)")
                return
            except Exception as e:
                log.error(f"HuggingFace initialization failed: {e}")

        raise RuntimeError(
            "Failed to initialize any embedding model. "
            "Install dependencies: pip install langchain-community fastembed"
        )

    def _init_supabase(self) -> None:
        """Initialize Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables are required"
            )

        self.supabase_client = create_client(supabase_url, supabase_key)
        log.info("✓ Supabase connection established")

    def upload_chunks(
        self,
        chunks: List[Dict],
        source_identifier: str,
        loader_type: str,
        batch_size: int = 50
    ) -> Tuple[int, int]:
        """
        Upload processed chunks to database.

        Args:
            chunks: List of chunk dicts with 'text' and 'metadata' keys
            source_identifier: URL or identifier of the source
            loader_type: Type of loader used (e.g., "Playwright", "Unstructured")
            batch_size: Number of chunks to upload in each batch

        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        if not chunks:
            log.warning("No chunks to upload")
            return 0, 0

        if not self.supabase_client:
            log.error("Supabase client not initialized")
            return 0, len(chunks)

        log.info(f"--> Uploading {len(chunks)} chunks to database...")

        # Convert chunks to DocumentChunk objects with embeddings
        doc_chunks = []
        for idx, chunk_data in enumerate(chunks, 1):
            chunk_text = chunk_data.get('text', '')
            chunk_meta = chunk_data.get('metadata', {})

            doc_chunk = DocumentChunk(
                content=chunk_text,
                source_url=source_identifier,
                chunk_index=idx,
                total_chunks=len(chunks),
                loader_type=loader_type,
                metadata=chunk_meta,
                scraped_at=datetime.now(timezone.utc)
            )
            doc_chunks.append(doc_chunk)

        # Generate embeddings
        log.debug(f"--> Generating embeddings for {len(doc_chunks)} chunks...")
        try:
            embeddings = self._generate_embeddings(
                [chunk.content for chunk in doc_chunks]
            )
            if len(embeddings) != len(doc_chunks):
                log.error(
                    f"Embedding count mismatch: {len(embeddings)} embeddings for {len(doc_chunks)} chunks"
                )
                return 0, len(doc_chunks)
        except Exception as e:
            log.error(f"--> Failed to generate embeddings: {e}")
            return 0, len(doc_chunks)

        # Upload in batches
        successful = 0
        failed = 0

        for i in range(0, len(doc_chunks), batch_size):
            batch_chunks = doc_chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            success, fail = self._upload_batch(
                batch_chunks, batch_embeddings, source_identifier
            )
            successful += success
            failed += fail

        log.info(
            f"--> ✅ Upload complete: {successful} successful, {failed} failed"
        )
        return successful, failed

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Uses local HuggingFace embeddings or embedding service microservice.
        OpenAI embeddings can be added in future versions if needed.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if self.use_local_embeddings:
            return self._generate_local_embeddings(texts)
        else:
            # Fallback to local embeddings to ensure uploads work
            logger.warning(
                "Remote embeddings not configured; falling back to local embeddings. "
                "Configure embedding service via EMBEDDING_SERVICE_URL to use remote."
            )
            self.use_local_embeddings = True
            return self._generate_local_embeddings(texts)

    def _generate_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using embedding service or local fallback."""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        log.debug(
            f"Generating {len(texts)} embeddings with {self.embedding_client_type}...")

        # Embedding service and LangChain models use embed_documents()
        if self.embedding_client_type in ["embedding_service", "fastembed", "huggingface"]:
            try:
                embeddings = self.embedding_model.embed_documents(texts)
                log.debug(f"✓ Generated {len(embeddings)} embeddings")
                return embeddings
            except Exception as e:
                log.error(f"Embedding generation failed: {e}")
                raise
        else:
            # Legacy path (should not be reached with new fallback chain)
            raise RuntimeError(
                f"Unsupported embedding client type: {self.embedding_client_type}")

    def _upload_batch(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        source_identifier: str
    ) -> Tuple[int, int]:
        """Upload a batch of chunks to Supabase."""
        if not chunks or not embeddings:
            return 0, 0

        # Prepare data for insertion
        records = []
        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "content": chunk.content,
                "source_url": chunk.source_url,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "embedding": embedding,
                # Persist loader_type inside metadata for traceability
                "metadata": {**(chunk.metadata or {}), **({"loader_type": chunk.loader_type} if chunk.loader_type else {})},
                "scraped_at": chunk.scraped_at.isoformat() if chunk.scraped_at else None,
            }
            records.append(record)

        # Upload to Supabase
        try:
            response = self.supabase_client.table(
                "document_chunks").insert(records).execute()

            successful = len(records)
            failed = 0

            log.debug(
                f"Batch upload successful: {successful} chunks to database"
            )
            return successful, failed

        except Exception as e:
            log.error(f"--> Batch upload failed: {e}")
            # Try uploading individually for better error reporting
            return self._upload_individual(chunks, embeddings)

    def _upload_individual(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> Tuple[int, int]:
        """Upload chunks individually for better error handling."""
        successful = 0
        failed = 0

        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "content": chunk.content,
                "source_url": chunk.source_url,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "embedding": embedding,
                "metadata": {**(chunk.metadata or {}), **({"loader_type": chunk.loader_type} if chunk.loader_type else {})},
                "scraped_at": chunk.scraped_at.isoformat() if chunk.scraped_at else None,
            }

            try:
                self.supabase_client.table(
                    "document_chunks").insert([record]).execute()
                successful += 1
            except Exception as e:
                log.warning(
                    f"Failed to upload chunk from {chunk.source_url}: {e}"
                )
                failed += 1

        return successful, failed

    def upload_links(
        self,
        links: List[str],
        source_url: str,
        loader_type: str = "Unknown"
    ) -> Tuple[int, int]:
        """
        Upload extracted links as searchable chunks.

        Links are stored in document_chunks with metadata marking them as extracted links.
        This makes them discoverable through vector search.

        Args:
            links: List of URLs extracted from the source
            source_url: The URL that was scraped
            loader_type: Type of loader used to extract the links

        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        if not links:
            log.debug(f"No links to upload from {source_url}")
            return 0, 0

        if not self.supabase_client:
            log.error("Supabase client not initialized")
            return 0, len(links)

        log.info(
            f"--> Uploading {len(links)} extracted links from {source_url}...")

        # Create link chunks - each link becomes a searchable chunk
        records = []
        for idx, link in enumerate(links, 1):
            # Create content that's useful for search: "Link: <url>"
            content = f"Link: {link}"

            embedding = self._generate_local_embeddings([link])[0]

            record = {
                "content": content,
                "source_url": source_url,  # Track where the link was found
                "chunk_index": idx,
                "total_chunks": len(links),
                "embedding": embedding,
                "metadata": {
                    "link_target": link,
                    "link_source": source_url,
                    "loader_type": loader_type,
                    "type": "extracted_link"  # Mark this as an extracted link
                },
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
            records.append(record)

        # Upload in batches
        successful = 0
        failed = 0
        batch_size = 50

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            try:
                response = self.supabase_client.table(
                    "document_chunks").insert(batch).execute()
                successful += len(batch)
                log.debug(f"Batch of {len(batch)} links uploaded successfully")
            except Exception as e:
                log.warning(f"Batch upload of links failed: {e}")
                # Try individual uploads
                for record in batch:
                    try:
                        self.supabase_client.table(
                            "document_chunks").insert([record]).execute()
                        successful += 1
                    except Exception as e2:
                        log.warning(
                            f"Failed to upload link {record['metadata']['link_target']}: {e2}"
                        )
                        failed += 1

        log.info(
            f"--> ✅ Links upload complete: {successful} successful, {failed} failed")
        return successful, failed

    def close(self) -> None:
        """Clean up resources."""
        log.debug("DatabaseUploader closing...")
