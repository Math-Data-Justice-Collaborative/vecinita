"""
Database uploader for the VECINA scraper.
Handles uploading processed document chunks to ChromaDB.
"""

import hashlib
import json
import logging
import os
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from urllib.parse import urlparse
from src.utils.tags import normalize_tags
from src.services.chroma_store import get_chroma_store, ChromaStore

try:
    from supabase import create_client  # type: ignore
    SUPABASE_AVAILABLE = True
except Exception:
    create_client = None  # type: ignore[assignment]
    SUPABASE_AVAILABLE = False

try:
    from pydantic import BaseModel, Field
    from langchain_openai import ChatOpenAI
    DEEPSEEK_TAGGING_AVAILABLE = True
except ImportError:
    DEEPSEEK_TAGGING_AVAILABLE = False

# Import embedding service client (preferred)
try:
    from src.embedding_service.client import create_embedding_client
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


class TagEnhancement(BaseModel):
    tags: List[str] = Field(default_factory=list)
    location_tags: List[str] = Field(default_factory=list)
    subject_tags: List[str] = Field(default_factory=list)
    service_tags: List[str] = Field(default_factory=list)
    content_type_tags: List[str] = Field(default_factory=list)
    organization_tags: List[str] = Field(default_factory=list)
    audience_tags: List[str] = Field(default_factory=list)
    document_title: Optional[str] = None
    source_summary: Optional[str] = None


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
    """Uploads processed chunks to Chroma vector database."""

    def __init__(self, use_local_embeddings: bool = True):
        """
        Initialize database uploader.

        Args:
            use_local_embeddings: If True, use embedding service (or fallback). If False, requires OpenAI API key.
        """
        self.use_local_embeddings = use_local_embeddings
        self.embedding_model = None
        self.embedding_client_type = None
        self.chroma_store: Optional[ChromaStore] = None
        self.deepseek_tagger = None
        self.deepseek_raw_model = None
        self._source_tag_cache: Dict[str, Dict[str, Any]] = {}
        self._known_tag_cache: Optional[List[str]] = None

        # Initialize embeddings with fallback chain
        if use_local_embeddings:
            self._init_embeddings()

        self._init_deepseek_tagger()

        # Initialize Chroma connection
        self._init_supabase()

    def _init_deepseek_tagger(self) -> None:
        """Initialize optional DeepSeek structured-output tag enhancer."""
        enabled = (os.getenv("ENABLE_DEEPSEEK_TAG_ENHANCEMENT", "true").lower() in {"1", "true", "yes"})
        if not enabled:
            return
        if not DEEPSEEK_TAGGING_AVAILABLE:
            return

        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            return

        try:
            deepseek_model = os.getenv("DEEPSEEK_TAG_MODEL", "deepseek-chat")
            deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            llm = ChatOpenAI(
                model=deepseek_model,
                api_key=deepseek_api_key,
                base_url=deepseek_base_url,
                temperature=0,
            )
            self.deepseek_raw_model = llm
            self.deepseek_tagger = llm.with_structured_output(TagEnhancement)
            log.info(f"✓ DeepSeek tag enhancement enabled ({deepseek_model})")
        except Exception as exc:
            log.warning(f"DeepSeek tag enhancement unavailable: {exc}")

    def _build_chunk_id(self, source_url: str, chunk_index: int) -> str:
        """Build deterministic chunk IDs so upsert updates existing records in place."""
        return hashlib.sha256(f"{source_url}:{chunk_index}".encode("utf-8")).hexdigest()

    def _source_locator(self, source_url: str) -> str:
        """Return host+path (including subdomain/path) for attribution displays."""
        try:
            parsed = urlparse(source_url or "")
            path = parsed.path or ""
            locator = f"{parsed.netloc}{path}".rstrip("/")
            return locator or parsed.netloc or source_url
        except Exception:
            return source_url

    def _build_chunk_metadata(self, metadata: Optional[Dict[str, Any]], tags: List[str]) -> Dict[str, Any]:
        result = dict(metadata) if isinstance(metadata, dict) else {}
        if tags:
            result["tags"] = tags
        else:
            result.pop("tags", None)
        return result

    def _normalize_tag_facets(self, payload: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
        data = payload if isinstance(payload, dict) else {}
        facets = {
            "location_tags": normalize_tags(data.get("location_tags", [])),
            "subject_tags": normalize_tags(data.get("subject_tags", [])),
            "service_tags": normalize_tags(data.get("service_tags", [])),
            "content_type_tags": normalize_tags(data.get("content_type_tags", [])),
            "organization_tags": normalize_tags(data.get("organization_tags", [])),
            "audience_tags": normalize_tags(data.get("audience_tags", [])),
        }
        return facets

    def _merge_all_tags(self, base_tags: List[str], facets: Dict[str, List[str]]) -> List[str]:
        combined: List[str] = list(base_tags or [])
        for values in facets.values():
            combined.extend(values or [])
        return normalize_tags(combined)

    def _enhance_source_tags(
        self,
        source_identifier: str,
        sample_texts: List[str],
        fallback_tags: List[str],
        known_tags: Optional[List[str]] = None,
    ) -> Tuple[List[str], Optional[str], Optional[str], Dict[str, List[str]]]:
        cached = self._source_tag_cache.get(source_identifier)
        if cached:
            return (
                normalize_tags(cached.get("tags", [])) or fallback_tags,
                cached.get("document_title"),
                cached.get("source_summary"),
                self._normalize_tag_facets(cached.get("tag_facets", {})),
            )

        if (not self.deepseek_tagger and not self.deepseek_raw_model) or not sample_texts:
            return fallback_tags, None, None, {}

        try:
            prompt = (
                "Generate retrieval metadata for a community-resource source. "
                "Return lowercase, search-friendly tags grouped by facets. "
                "Include concrete terms when available (e.g., city/neighborhood, health, insurance, legal assistance, housing, food, employment, education, immigration, benefits, transportation, childcare). "
                "For content style, prefer tags like how-to, tutorial, faq, checklist, guide, form, directory, contact. "
                "For organization context, include org type/context tags (nonprofit, government, clinic, school, legal-aid, coalition, community-center). "
                "Do not invent facts; use only supported inferences from URL/content.\n\n"
                "Output schema keys: tags, location_tags, subject_tags, service_tags, content_type_tags, organization_tags, audience_tags, document_title, source_summary.\n\n"
                f"Source URL: {source_identifier}\n\n"
                + (f"Existing preferred tags (reuse when relevant): {', '.join((known_tags or [])[:120])}\n\n" if known_tags else "")
                +
                "Sample content:\n"
                + "\n\n".join(sample_texts[:3])
            )
            structured = None
            if self.deepseek_tagger:
                structured = self.deepseek_tagger.invoke(prompt)
            if isinstance(structured, dict):
                raw_tags = structured.get("tags", [])
                facets = self._normalize_tag_facets(structured)
                title = structured.get("document_title")
                summary = structured.get("source_summary")
            else:
                raw_tags = getattr(structured, "tags", [])
                facets = self._normalize_tag_facets(
                    {
                        "location_tags": getattr(structured, "location_tags", []),
                        "subject_tags": getattr(structured, "subject_tags", []),
                        "service_tags": getattr(structured, "service_tags", []),
                        "content_type_tags": getattr(structured, "content_type_tags", []),
                        "organization_tags": getattr(structured, "organization_tags", []),
                        "audience_tags": getattr(structured, "audience_tags", []),
                    }
                )
                title = getattr(structured, "document_title", None)
                summary = getattr(structured, "source_summary", None)

            enhanced_tags = normalize_tags(raw_tags)
            enhanced_tags = self._merge_all_tags(enhanced_tags, facets)
            final_tags = normalize_tags((known_tags or []) + enhanced_tags + fallback_tags)
            self._source_tag_cache[source_identifier] = {
                "tags": final_tags,
                "document_title": title,
                "source_summary": summary,
                "tag_facets": facets,
            }
            return final_tags, title, summary, facets
        except Exception as exc:
            if self.deepseek_raw_model and "response_format" in str(exc).lower():
                try:
                    fallback_prompt = (
                        "Return strict JSON object only with keys: tags, location_tags, subject_tags, service_tags, content_type_tags, organization_tags, audience_tags, document_title, source_summary. "
                        "All tag arrays should contain lowercase strings suitable for search. "
                        "Do not include markdown.\n\n"
                        f"Source URL: {source_identifier}\n\n"
                        "Sample content:\n"
                        + "\n\n".join(sample_texts[:3])
                    )
                    response = self.deepseek_raw_model.invoke(fallback_prompt)
                    content = getattr(response, "content", "") if response else ""
                    if isinstance(content, list):
                        content = "\n".join(str(part) for part in content)
                    payload = json.loads(str(content).strip())
                    structured = TagEnhancement.model_validate(payload)
                    facets = self._normalize_tag_facets(payload)
                    final_tags = normalize_tags(
                        (known_tags or [])
                        + self._merge_all_tags(normalize_tags(structured.tags), facets)
                        + fallback_tags
                    )
                    self._source_tag_cache[source_identifier] = {
                        "tags": final_tags,
                        "document_title": structured.document_title,
                        "source_summary": structured.source_summary,
                        "tag_facets": facets,
                    }
                    return final_tags, structured.document_title, structured.source_summary, facets
                except Exception as fallback_exc:
                    log.warning(f"DeepSeek JSON fallback failed for {source_identifier}: {fallback_exc}")
            log.warning(f"DeepSeek tag enhancement failed for {source_identifier}: {exc}")
            return fallback_tags, None, None, {}

    def _get_known_tags(self) -> List[str]:
        """Load existing tags from source records for tag reuse/canonicalization."""
        if self._known_tag_cache is not None:
            return self._known_tag_cache

        if not self.chroma_store:
            self._known_tag_cache = []
            return self._known_tag_cache

        try:
            known: List[str] = []
            for source in self.chroma_store.list_sources(limit=5000, offset=0):
                source_tags = normalize_tags((source or {}).get("tags", []))
                if source_tags:
                    known.extend(source_tags)
            self._known_tag_cache = normalize_tags(known)
        except Exception as exc:
            log.debug(f"Unable to load known tag catalog: {exc}")
            self._known_tag_cache = []
        return self._known_tag_cache

    def _init_embeddings(self) -> None:
        """Initialize embedding model with fallback chain: Service → FastEmbed → HuggingFace."""
        strict_startup = (
            os.getenv("EMBEDDING_STRICT_STARTUP", "true").lower() in {"1", "true", "yes"}
        )

        # Try embedding service first (lightweight, scalable)
        embedding_service_url = os.getenv(
            "EMBEDDING_SERVICE_URL", "http://embedding-service:8001")

        if EMBEDDING_SERVICE_AVAILABLE:
            try:
                log.info(
                    f"Initializing Embedding Service client ({embedding_service_url})...")
                self.embedding_model = create_embedding_client(
                    embedding_service_url,
                    validate_on_init=True,
                )
                self.embedding_client_type = "embedding_service"
                log.info(
                    f"✓ Embedding Service client initialized (384 dimensions)")
                return
            except Exception as e:
                log.warning(f"Embedding Service initialization failed: {e}")
                if strict_startup:
                    raise RuntimeError(
                        "Embedding service validation failed during scraper uploader startup. "
                        "Set EMBEDDING_SERVICE_URL to a reachable Modal endpoint, or set "
                        "EMBEDDING_STRICT_STARTUP=false only for local development fallbacks."
                    ) from e

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
        """Initialize Chroma client store.

        Kept method name for backward compatibility in tests/import paths.
        """
        self.chroma_store = get_chroma_store()
        if not self.chroma_store.heartbeat():
            log.warning("Chroma heartbeat failed during uploader init; uploads will retry on use")
        else:
            log.info("✓ Chroma connection established")

    def upload_chunks(
        self,
        chunks: List[Dict],
        source_identifier: str,
        loader_type: str,
        source_tags: Optional[List[str]] = None,
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

        if not self.chroma_store:
            log.error("Chroma store not initialized")
            return 0, len(chunks)

        log.info(f"--> Uploading {len(chunks)} chunks to database...")

        resolved_source_tags = normalize_tags(source_tags)
        existing_source_tags = self._get_source_tags(source_identifier)
        resolved_source_tags = normalize_tags((resolved_source_tags or []) + existing_source_tags)
        known_tags = self._get_known_tags()

        sample_texts = [
            str(chunk.get("text") or "").strip()
            for chunk in chunks[:3]
            if str(chunk.get("text") or "").strip()
        ]
        resolved_source_tags, source_title, source_summary, source_tag_facets = self._enhance_source_tags(
            source_identifier,
            sample_texts,
            resolved_source_tags,
            known_tags=known_tags,
        )

        # Convert chunks to DocumentChunk objects with embeddings
        doc_chunks = []
        for idx, chunk_data in enumerate(chunks, 1):
            chunk_text = chunk_data.get('text', '')
            chunk_meta = chunk_data.get('metadata', {})
            chunk_tags = normalize_tags((chunk_meta or {}).get("tags", []))
            chunk_facet_tags = self._normalize_tag_facets(chunk_meta)
            final_tags = self._merge_all_tags(chunk_tags, chunk_facet_tags) or resolved_source_tags
            chunk_meta = self._build_chunk_metadata(chunk_meta, final_tags)
            if source_title and not chunk_meta.get("document_title"):
                chunk_meta["document_title"] = source_title
            if source_summary and not chunk_meta.get("source_summary"):
                chunk_meta["source_summary"] = source_summary
            for facet_name, facet_values in source_tag_facets.items():
                if facet_values and not normalize_tags(chunk_meta.get(facet_name, [])):
                    chunk_meta[facet_name] = facet_values

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
            log.warning(
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
        """Upload a batch of chunks to Chroma."""
        if not chunks or not embeddings:
            return 0, 0

        rows = []
        for chunk, embedding in zip(chunks, embeddings):
            row_id = self._build_chunk_id(chunk.source_url, chunk.chunk_index)
            metadata = dict(chunk.metadata or {})
            metadata["source_locator"] = self._source_locator(chunk.source_url)
            row = {
                "id": row_id,
                "content": chunk.content,
                "source_url": chunk.source_url,
                "source_domain": metadata.get("source_locator", ""),
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "embedding": embedding,
                "metadata": {**metadata, **({"loader_type": chunk.loader_type} if chunk.loader_type else {})},
                "scraped_at": chunk.scraped_at.isoformat() if chunk.scraped_at else None,
                "created_at": (chunk.scraped_at or datetime.now(timezone.utc)).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "document_title": metadata.get("document_title", ""),
                "chunk_size": len(chunk.content or ""),
                "is_processed": True,
                "processing_status": "completed",
            }
            rows.append(row)

        try:
            successful = self.chroma_store.upsert_chunks(rows)
            failed = 0
            log.debug(f"Batch upload successful: {successful} chunks to Chroma")
            return successful, failed

        except Exception as e:
            log.error(f"--> Batch upload failed: {e}")
            # Try uploading individually for better error reporting
            return self._upload_individual(chunks, embeddings)

    def _get_source_tags(self, source_identifier: str) -> List[str]:
        """Fetch canonical source-level tags from Chroma source records."""
        if not self.chroma_store:
            return []
        try:
            source = self.chroma_store.get_source(source_identifier)
            if not source:
                return []
            metadata = source.get("metadata") if isinstance(source, dict) else {}
            if isinstance(metadata, dict):
                return normalize_tags(metadata.get("tags", []))
        except Exception as exc:
            log.debug(f"Unable to load source tags for {source_identifier}: {exc}")
        return []

    def _upload_individual(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> Tuple[int, int]:
        """Upload chunks individually for better error handling."""
        successful = 0
        failed = 0

        for chunk, embedding in zip(chunks, embeddings):
            metadata = dict(chunk.metadata or {})
            metadata["source_locator"] = self._source_locator(chunk.source_url)
            row = {
                "id": self._build_chunk_id(chunk.source_url, chunk.chunk_index),
                "content": chunk.content,
                "source_url": chunk.source_url,
                "source_domain": metadata.get("source_locator", ""),
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "embedding": embedding,
                "metadata": {**metadata, **({"loader_type": chunk.loader_type} if chunk.loader_type else {})},
                "scraped_at": chunk.scraped_at.isoformat() if chunk.scraped_at else None,
                "created_at": (chunk.scraped_at or datetime.now(timezone.utc)).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "document_title": metadata.get("document_title", ""),
                "chunk_size": len(chunk.content or ""),
                "is_processed": True,
                "processing_status": "completed",
            }

            try:
                self.chroma_store.upsert_chunks([row])
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

        if not self.chroma_store:
            log.error("Chroma store not initialized")
            return 0, len(links)

        log.info(
            f"--> Uploading {len(links)} extracted links from {source_url}...")

        # Create link chunks - each link becomes a searchable chunk
        rows = []
        for idx, link in enumerate(links, 1):
            # Create content that's useful for search: "Link: <url>"
            content = f"Link: {link}"

            embedding = self._generate_local_embeddings([link])[0]

            row = {
                "id": hashlib.sha256(f"{source_url}:{idx}:{content}".encode("utf-8")).hexdigest(),
                "content": content,
                "source_url": source_url,  # Track where the link was found
                "source_domain": self._source_locator(source_url),
                "chunk_index": idx,
                "total_chunks": len(links),
                "embedding": embedding,
                "metadata": {
                    "link_target": link,
                    "link_source": source_url,
                    "source_locator": self._source_locator(source_url),
                    "loader_type": loader_type,
                    "type": "extracted_link"  # Mark this as an extracted link
                },
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "document_title": "",
                "chunk_size": len(content),
                "is_processed": True,
                "processing_status": "completed",
            }
            rows.append(row)

        # Upload in batches
        successful = 0
        failed = 0
        batch_size = 50

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            try:
                successful += self.chroma_store.upsert_chunks(batch)
                log.debug(f"Batch of {len(batch)} links uploaded successfully")
            except Exception as e:
                log.warning(f"Batch upload of links failed: {e}")
                # Try individual uploads
                for row in batch:
                    try:
                        self.chroma_store.upsert_chunks([row])
                        successful += 1
                    except Exception as e2:
                        log.warning(
                            f"Failed to upload link {row['metadata']['link_target']}: {e2}"
                        )
                        failed += 1

        log.info(
            f"--> ✅ Links upload complete: {successful} successful, {failed} failed")
        return successful, failed

    def close(self) -> None:
        """Clean up resources."""
        log.debug("DatabaseUploader closing...")
