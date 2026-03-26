"""
Database uploader for the VECINA scraper.
Handles uploading processed document chunks to ChromaDB.
"""

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, cast
from urllib.parse import urlparse

from src.services.chroma_store import ChromaStore, get_chroma_store
from src.utils.tags import build_bilingual_tag_fields, infer_tags_from_text, normalize_tags

try:
    from supabase import create_client

    SUPABASE_AVAILABLE = True
except Exception:
    create_client = None  # type: ignore[assignment]
    SUPABASE_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel, Field

    DEEPSEEK_TAGGING_AVAILABLE = True
except ImportError:
    DEEPSEEK_TAGGING_AVAILABLE = False

try:
    from langchain_groq import ChatGroq

    GROQ_TAGGING_AVAILABLE = True
except ImportError:
    ChatGroq = None
    GROQ_TAGGING_AVAILABLE = False

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

log = logging.getLogger("vecinita_pipeline.uploader")
log.addHandler(logging.NullHandler())


class TagEnhancement(BaseModel):
    tags: list[str] = Field(default_factory=list)
    location_tags: list[str] = Field(default_factory=list)
    subject_tags: list[str] = Field(default_factory=list)
    service_tags: list[str] = Field(default_factory=list)
    content_type_tags: list[str] = Field(default_factory=list)
    organization_tags: list[str] = Field(default_factory=list)
    audience_tags: list[str] = Field(default_factory=list)
    document_title: str | None = None
    source_summary: str | None = None


@dataclass
class DocumentChunk:
    """Represents a single document chunk with metadata."""

    content: str
    source_url: str
    chunk_index: int
    total_chunks: int | None = None
    loader_type: str | None = None
    metadata: dict | None = None
    scraped_at: datetime | None = None


class DatabaseUploader:
    """Uploads processed chunks to Chroma vector database."""

    def __init__(self, use_local_embeddings: bool = True):
        """
        Initialize database uploader.

        Args:
            use_local_embeddings: If True, use embedding service (or fallback). If False, requires OpenAI API key.
        """
        self.use_local_embeddings = use_local_embeddings
        self.embedding_model: Any | None = None
        self.embedding_client_type: str | None = None
        self.chroma_store: ChromaStore | None = None
        self.deepseek_tagger = None
        self.deepseek_raw_model = None
        self._llm_structured_output_supported = True
        self._llm_structured_output_warned = False
        self._source_tag_cache: dict[str, dict[str, Any]] = {}
        self._known_tag_cache: list[str] | None = None
        self.supabase_client: Any | None = None
        self.vector_sync_enabled = os.getenv("VECTOR_SYNC_ENABLED", "true").lower() in {
            "1",
            "true",
            "yes",
        }
        self.vector_sync_degraded_mode = os.getenv("VECTOR_SYNC_DEGRADED_MODE", "true").lower() in {
            "1",
            "true",
            "yes",
        }
        self.vector_sync_retry_max = max(1, int(os.getenv("VECTOR_SYNC_RETRY_MAX", "3")))
        self.vector_sync_retry_delay_seconds = max(
            1, int(os.getenv("VECTOR_SYNC_RETRY_DELAY_SECONDS", "2"))
        )
        self.vector_sync_table = os.getenv("VECTOR_SYNC_SUPABASE_TABLE", "document_chunks")
        self.vector_sync_schema = (
            os.getenv("VECTOR_SYNC_SUPABASE_SCHEMA", "public").strip() or "public"
        )
        self.vector_sync_pending_rows: list[dict[str, Any]] = []

        # Initialize embeddings with fallback chain
        if use_local_embeddings:
            self._init_embeddings()

        self._init_deepseek_tagger()

        # Initialize Chroma connection
        self._init_supabase()

    def _init_deepseek_tagger(self) -> None:
        """Initialize optional LLM structured-output tag enhancer.

        Provider selection:
        - auto (default): DeepSeek first, then Groq fallback
        - deepseek: DeepSeek only
        - groq: Groq only
        """
        enabled = os.getenv(
            "ENABLE_LLM_TAG_ENHANCEMENT", os.getenv("ENABLE_DEEPSEEK_TAG_ENHANCEMENT", "true")
        ).lower() in {"1", "true", "yes"}
        if not enabled:
            return

        provider = os.getenv("LLM_TAG_PROVIDER", "auto").strip().lower()

        if provider in {"auto", "deepseek"} and DEEPSEEK_TAGGING_AVAILABLE:
            deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
            if deepseek_api_key:
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
                    log.info(f"✓ LLM tag enhancement enabled via DeepSeek ({deepseek_model})")
                    return
                except Exception as exc:
                    log.warning(f"DeepSeek tag enhancement unavailable: {exc}")
            elif provider == "deepseek":
                log.warning(
                    "DeepSeek tag enhancement requested but DEEPSEEK_API_KEY is not configured"
                )

        if provider in {"auto", "groq"} and GROQ_TAGGING_AVAILABLE:
            groq_api_key = os.getenv("GROQ_API_KEY")
            if groq_api_key:
                try:
                    groq_model = os.getenv("GROQ_TAG_MODEL", "llama-3.1-8b-instant")
                    llm = ChatGroq(
                        model=groq_model,
                        api_key=groq_api_key,
                        temperature=0,
                    )
                    self.deepseek_raw_model = llm
                    self.deepseek_tagger = llm.with_structured_output(TagEnhancement)
                    log.info(f"✓ LLM tag enhancement enabled via Groq ({groq_model})")
                    return
                except Exception as exc:
                    log.warning(f"Groq tag enhancement unavailable: {exc}")
            elif provider == "groq":
                log.warning("Groq tag enhancement requested but GROQ_API_KEY is not configured")

        log.info("LLM tag enhancement disabled: no configured provider credentials available")

    def _build_chunk_id(self, source_url: str, chunk_index: int) -> str:
        """Build deterministic chunk IDs so upsert updates existing records in place."""
        return hashlib.sha256(f"{source_url}:{chunk_index}".encode()).hexdigest()

    def _source_locator(self, source_url: str) -> str:
        """Return host+path (including subdomain/path) for attribution displays."""
        try:
            parsed = urlparse(source_url or "")
            path = parsed.path or ""
            locator = f"{parsed.netloc}{path}".rstrip("/")
            return locator or parsed.netloc or source_url
        except Exception:
            return source_url

    def _build_chunk_metadata(
        self, metadata: dict[str, Any] | None, tags: list[str]
    ) -> dict[str, Any]:
        result = dict(metadata) if isinstance(metadata, dict) else {}
        if tags:
            result["tags"] = tags
        else:
            result.pop("tags", None)
        return result

    def _normalize_tag_facets(self, payload: dict[str, Any] | None) -> dict[str, list[str]]:
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

    def _merge_all_tags(self, base_tags: list[str], facets: dict[str, list[str]]) -> list[str]:
        combined: list[str] = list(base_tags or [])
        for values in facets.values():
            combined.extend(values or [])
        return normalize_tags(combined)

    def _parse_llm_json_payload(self, content: Any) -> dict[str, Any] | None:
        text = content
        if isinstance(text, list):
            text = "\n".join(str(part) for part in text)
        text = str(text or "").strip()
        if not text:
            return None

        try:
            payload = json.loads(text)
            return payload if isinstance(payload, dict) else None
        except Exception:
            pass

        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1).strip()
            try:
                payload = json.loads(candidate)
                return payload if isinstance(payload, dict) else None
            except Exception:
                return None

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1].strip()
            try:
                payload = json.loads(candidate)
                return payload if isinstance(payload, dict) else None
            except Exception:
                return None

        return None

    def _invoke_raw_json_tagger(
        self,
        *,
        source_identifier: str,
        sample_texts: list[str],
        known_tags: list[str] | None = None,
    ) -> tuple[TagEnhancement, dict[str, list[str]]] | None:
        if not self.deepseek_raw_model:
            return None

        prompt = (
            "Return strict JSON object only with keys: tags, location_tags, subject_tags, service_tags, content_type_tags, organization_tags, audience_tags, document_title, source_summary. "
            "All tag arrays should contain lowercase strings suitable for search. "
            "Do not include markdown.\n\n"
            f"Source URL: {source_identifier}\n\n"
            + (
                f"Existing preferred tags (reuse when relevant): {', '.join((known_tags or [])[:120])}\n\n"
                if known_tags
                else ""
            )
            + "Sample content:\n"
            + "\n\n".join(sample_texts[:3])
        )

        response = self.deepseek_raw_model.invoke(prompt)
        content = getattr(response, "content", "") if response else ""
        payload = self._parse_llm_json_payload(content)
        if not payload:
            return None

        structured = TagEnhancement.model_validate(payload)
        facets = self._normalize_tag_facets(payload)
        return structured, facets

    def _enhance_source_tags(
        self,
        source_identifier: str,
        sample_texts: list[str],
        fallback_tags: list[str],
        known_tags: list[str] | None = None,
    ) -> tuple[list[str], str | None, str | None, dict[str, list[str]]]:
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
                + (
                    f"Existing preferred tags (reuse when relevant): {', '.join((known_tags or [])[:120])}\n\n"
                    if known_tags
                    else ""
                )
                + "Sample content:\n"
                + "\n\n".join(sample_texts[:3])
            )
            structured = None
            facets: dict[str, list[str]]
            if self.deepseek_tagger and self._llm_structured_output_supported:
                structured = self.deepseek_tagger.invoke(prompt)
            elif self.deepseek_raw_model:
                raw_result = self._invoke_raw_json_tagger(
                    source_identifier=source_identifier,
                    sample_texts=sample_texts,
                    known_tags=known_tags,
                )
                if raw_result is not None:
                    structured, facets = raw_result
                else:
                    return fallback_tags, None, None, {}

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
                self._llm_structured_output_supported = False
                if not self._llm_structured_output_warned:
                    log.info(
                        "LLM structured output unavailable; switching to raw JSON tagging mode for remaining sources"
                    )
                    self._llm_structured_output_warned = True
                try:
                    raw_result = self._invoke_raw_json_tagger(
                        source_identifier=source_identifier,
                        sample_texts=sample_texts,
                        known_tags=known_tags,
                    )
                    if raw_result is None:
                        log.debug(
                            "Raw JSON fallback produced no parseable payload for %s",
                            source_identifier,
                        )
                        return fallback_tags, None, None, {}
                    structured, facets = raw_result
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
                    log.debug(
                        f"DeepSeek JSON fallback failed for {source_identifier}: {fallback_exc}"
                    )
            log.warning(f"DeepSeek tag enhancement failed for {source_identifier}: {exc}")
            return fallback_tags, None, None, {}

    def _get_known_tags(self) -> list[str]:
        """Load existing tags from source records for tag reuse/canonicalization."""
        if self._known_tag_cache is not None:
            return self._known_tag_cache

        if not self.chroma_store:
            self._known_tag_cache = []
            return self._known_tag_cache

        try:
            known: list[str] = []
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
        strict_startup = os.getenv("EMBEDDING_STRICT_STARTUP", "true").lower() in {
            "1",
            "true",
            "yes",
        }

        # Try embedding service first (lightweight, scalable)
        embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8001")

        if EMBEDDING_SERVICE_AVAILABLE:
            try:
                log.info(f"Initializing Embedding Service client ({embedding_service_url})...")
                self.embedding_model = create_embedding_client(
                    embedding_service_url,
                    validate_on_init=True,
                )
                self.embedding_client_type = "embedding_service"
                log.info("✓ Embedding Service client initialized (384 dimensions)")
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
                self.embedding_model = FastEmbedEmbeddings(model_name="fast-bge-small-en-v1.5")
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

        if not self.vector_sync_enabled:
            log.info("Supabase sync disabled (VECTOR_SYNC_ENABLED=false)")
            return

        if not SUPABASE_AVAILABLE or create_client is None:
            log.warning("Supabase sync unavailable: supabase client dependency is not installed")
            return

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = (
            os.getenv("SUPABASE_SECRET_KEY")
            or os.getenv("SUPABASE_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        )

        if not supabase_url or not supabase_key:
            log.warning("Supabase sync unavailable: missing SUPABASE_URL or SUPABASE_KEY")
            return

        try:
            self.supabase_client = create_client(supabase_url, supabase_key)
            log.info("✓ Supabase sync client initialized")
        except Exception as exc:
            self.supabase_client = None
            log.warning(f"Supabase sync client initialization failed: {exc}")

    def _build_supabase_row(self, row: dict[str, Any]) -> dict[str, Any]:
        metadata = dict(row.get("metadata") or {})
        return {
            "id": row.get("id"),
            "content": row.get("content") or "",
            "source_url": row.get("source_url") or metadata.get("source_url") or "",
            "source_domain": row.get("source_domain") or metadata.get("source_domain") or "",
            "chunk_index": int(row.get("chunk_index") or metadata.get("chunk_index") or 0),
            "total_chunks": int(row.get("total_chunks") or metadata.get("total_chunks") or 0),
            "chunk_size": int(
                row.get("chunk_size")
                or metadata.get("chunk_size")
                or len(str(row.get("content") or ""))
            ),
            "document_title": row.get("document_title") or metadata.get("document_title") or "",
            "metadata": metadata,
            "embedding": row.get("embedding") or [],
            "processing_status": row.get("processing_status") or "completed",
            "is_processed": bool(row.get("is_processed", True)),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "scraped_at": row.get("scraped_at"),
        }

    def _queue_sync_rows(self, rows: list[dict[str, Any]], error: Exception) -> None:
        if not self.vector_sync_enabled:
            return
        if not rows:
            return
        self.vector_sync_pending_rows.extend([self._build_supabase_row(row) for row in rows])
        log.warning(
            "Queued %s row(s) for Supabase sync replay after failure: %s",
            len(rows),
            error,
        )

    def _supabase_table_client(self):
        if not self.supabase_client:
            return None
        try:
            if self.vector_sync_schema:
                return self.supabase_client.schema(self.vector_sync_schema).table(
                    self.vector_sync_table
                )
            return self.supabase_client.table(self.vector_sync_table)
        except Exception:
            return self.supabase_client.table(self.vector_sync_table)

    def _apply_supabase_schema_fallback(self, error: Exception) -> bool:
        err = str(error)
        if "PGRST106" not in err:
            return False
        if "graphql_public" in err and self.vector_sync_schema != "graphql_public":
            self.vector_sync_schema = "graphql_public"
            log.warning(
                "Supabase sync switched schema to 'graphql_public' after PGRST106; set VECTOR_SYNC_SUPABASE_SCHEMA=graphql_public to persist"
            )
            return True
        return False

    def _handle_unrecoverable_sync_error(self, error: Exception) -> bool:
        err = str(error)
        if "PGRST205" in err and "Could not find the table" in err:
            self.vector_sync_enabled = False
            self.vector_sync_pending_rows.clear()
            log.warning(
                "Supabase sync disabled for this run: table '%s.%s' is unavailable (%s)",
                self.vector_sync_schema,
                self.vector_sync_table,
                error,
            )
            return True
        return False

    def _flush_sync_queue(self) -> None:
        if not self.supabase_client or not self.vector_sync_pending_rows:
            return

        queued = list(self.vector_sync_pending_rows)
        try:
            table_client = self._supabase_table_client()
            if table_client is None:
                return
            table_client.upsert(queued, on_conflict="id").execute()
            self.vector_sync_pending_rows.clear()
            log.info("Flushed %s queued Supabase sync row(s)", len(queued))
        except Exception as exc:
            if self._apply_supabase_schema_fallback(exc):
                try:
                    table_client = self._supabase_table_client()
                    if table_client is None:
                        return
                    table_client.upsert(queued, on_conflict="id").execute()
                    self.vector_sync_pending_rows.clear()
                    log.info("Flushed %s queued Supabase sync row(s)", len(queued))
                    return
                except Exception as retry_exc:
                    if self._handle_unrecoverable_sync_error(retry_exc):
                        return
                    log.warning(
                        "Supabase sync replay failed (%s queued rows retained): %s",
                        len(queued),
                        retry_exc,
                    )
                    return
            if self._handle_unrecoverable_sync_error(exc):
                return
            log.warning(
                "Supabase sync replay failed (%s queued rows retained): %s", len(queued), exc
            )

    def _sync_rows_to_supabase(self, rows: list[dict[str, Any]]) -> bool:
        if not rows or not self.vector_sync_enabled:
            return True
        if not self.supabase_client:
            return True

        self._flush_sync_queue()
        payload = [self._build_supabase_row(row) for row in rows]
        last_error: Exception | None = None
        for attempt in range(1, self.vector_sync_retry_max + 1):
            try:
                table_client = self._supabase_table_client()
                if table_client is None:
                    return True
                table_client.upsert(payload, on_conflict="id").execute()
                return True
            except Exception as exc:
                if self._apply_supabase_schema_fallback(exc):
                    try:
                        table_client = self._supabase_table_client()
                        if table_client is None:
                            return True
                        table_client.upsert(payload, on_conflict="id").execute()
                        return True
                    except Exception as retry_exc:
                        if self._handle_unrecoverable_sync_error(retry_exc):
                            return False
                        exc = retry_exc
                if self._handle_unrecoverable_sync_error(exc):
                    return False
                last_error = exc
                if attempt < self.vector_sync_retry_max:
                    sleep_seconds = self.vector_sync_retry_delay_seconds * attempt
                    log.warning(
                        "Supabase sync attempt %s/%s failed, retrying in %ss: %s",
                        attempt,
                        self.vector_sync_retry_max,
                        sleep_seconds,
                        exc,
                    )
                    time.sleep(sleep_seconds)

        if last_error is not None:
            self._queue_sync_rows(rows, last_error)
            if not self.vector_sync_degraded_mode:
                raise RuntimeError(f"Supabase sync failed after retries: {last_error}")
            log.warning("Supabase sync failed in degraded mode; write kept in Chroma only")
        return False

    def upload_chunks(
        self,
        chunks: list[dict],
        source_identifier: str,
        loader_type: str,
        source_tags: list[str] | None = None,
        batch_size: int = 50,
    ) -> tuple[int, int]:
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
        inferred_source_tags = infer_tags_from_text("\n\n".join(sample_texts), max_tags=12)
        resolved_source_tags = normalize_tags((resolved_source_tags or []) + inferred_source_tags)
        resolved_source_tags, source_title, source_summary, source_tag_facets = (
            self._enhance_source_tags(
                source_identifier,
                sample_texts,
                resolved_source_tags,
                known_tags=known_tags,
            )
        )
        source_bilingual_tags = build_bilingual_tag_fields(resolved_source_tags)

        # Convert chunks to DocumentChunk objects with embeddings
        doc_chunks = []
        for idx, chunk_data in enumerate(chunks, 1):
            chunk_text = chunk_data.get("text", "")
            chunk_meta = chunk_data.get("metadata", {})
            chunk_tags = normalize_tags((chunk_meta or {}).get("tags", []))
            chunk_facet_tags = self._normalize_tag_facets(chunk_meta)
            final_tags = normalize_tags(
                (resolved_source_tags or []) + self._merge_all_tags(chunk_tags, chunk_facet_tags)
            )
            chunk_meta = self._build_chunk_metadata(chunk_meta, final_tags)
            if source_title and not chunk_meta.get("document_title"):
                chunk_meta["document_title"] = source_title
            if source_summary and not chunk_meta.get("source_summary"):
                chunk_meta["source_summary"] = source_summary
            if source_bilingual_tags.get("tags_en"):
                chunk_meta["tags_en"] = source_bilingual_tags["tags_en"]
            if source_bilingual_tags.get("tags_es"):
                chunk_meta["tags_es"] = source_bilingual_tags["tags_es"]
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
                scraped_at=datetime.now(timezone.utc),
            )
            doc_chunks.append(doc_chunk)

        # Generate embeddings
        log.debug(f"--> Generating embeddings for {len(doc_chunks)} chunks...")
        try:
            embeddings = self._generate_embeddings([chunk.content for chunk in doc_chunks])
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
            batch_chunks = doc_chunks[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]

            success, fail = self._upload_batch(batch_chunks, batch_embeddings, source_identifier)
            successful += success
            failed += fail

        log.info(f"--> ✅ Upload complete: {successful} successful, {failed} failed")
        return successful, failed

    def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
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

    def _generate_local_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using embedding service or local fallback."""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        log.debug(f"Generating {len(texts)} embeddings with {self.embedding_client_type}...")

        # Embedding service and LangChain models use embed_documents()
        if self.embedding_client_type in ["embedding_service", "fastembed", "huggingface"]:
            try:
                embeddings = self.embedding_model.embed_documents(texts)
                log.debug(f"✓ Generated {len(embeddings)} embeddings")
                return cast(list[list[float]], embeddings)
            except Exception as e:
                log.error(f"Embedding generation failed: {e}")
                raise
        else:
            # Legacy path (should not be reached with new fallback chain)
            raise RuntimeError(f"Unsupported embedding client type: {self.embedding_client_type}")

    def _upload_batch(
        self, chunks: list[DocumentChunk], embeddings: list[list[float]], source_identifier: str
    ) -> tuple[int, int]:
        """Upload a batch of chunks to Chroma."""
        if not chunks or not embeddings:
            return 0, 0

        if self.chroma_store is None:
            raise RuntimeError("Chroma store not initialized")

        rows = []
        for chunk, embedding in zip(chunks, embeddings, strict=False):
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
                "metadata": {
                    **metadata,
                    **({"loader_type": chunk.loader_type} if chunk.loader_type else {}),
                },
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
            self._sync_rows_to_supabase(rows)
            failed = 0
            log.debug(f"Batch upload successful: {successful} chunks to Chroma")
            return successful, failed

        except Exception as e:
            log.error(f"--> Batch upload failed: {e}")
            # Try uploading individually for better error reporting
            return self._upload_individual(chunks, embeddings)

    def _get_source_tags(self, source_identifier: str) -> list[str]:
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
        self, chunks: list[DocumentChunk], embeddings: list[list[float]]
    ) -> tuple[int, int]:
        """Upload chunks individually for better error handling."""
        if self.chroma_store is None:
            raise RuntimeError("Chroma store not initialized")

        successful = 0
        failed = 0

        for chunk, embedding in zip(chunks, embeddings, strict=False):
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
                "metadata": {
                    **metadata,
                    **({"loader_type": chunk.loader_type} if chunk.loader_type else {}),
                },
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
                self._sync_rows_to_supabase([row])
                successful += 1
            except Exception as e:
                log.warning(f"Failed to upload chunk from {chunk.source_url}: {e}")
                failed += 1

        return successful, failed

    def upload_links(
        self, links: list[str], source_url: str, loader_type: str = "Unknown"
    ) -> tuple[int, int]:
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

        log.info(f"--> Uploading {len(links)} extracted links from {source_url}...")

        # Create link chunks - each link becomes a searchable chunk
        rows = []
        for idx, link in enumerate(links, 1):
            # Create content that's useful for search: "Link: <url>"
            content = f"Link: {link}"

            embedding = self._generate_local_embeddings([link])[0]

            row = {
                "id": hashlib.sha256(f"{source_url}:{idx}:{content}".encode()).hexdigest(),
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
                    "type": "extracted_link",  # Mark this as an extracted link
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
            batch = rows[i : i + batch_size]

            try:
                successful += self.chroma_store.upsert_chunks(batch)
                self._sync_rows_to_supabase(batch)
                log.debug(f"Batch of {len(batch)} links uploaded successfully")
            except Exception as e:
                log.warning(f"Batch upload of links failed: {e}")
                # Try individual uploads
                for row in batch:
                    try:
                        self.chroma_store.upsert_chunks([row])
                        self._sync_rows_to_supabase([row])
                        successful += 1
                    except Exception as e2:
                        metadata = row.get("metadata") if isinstance(row, dict) else None
                        link_target = (
                            metadata.get("link_target") if isinstance(metadata, dict) else "unknown"
                        )
                        log.warning(f"Failed to upload link {link_target}: {e2}")
                        failed += 1

        log.info(f"--> ✅ Links upload complete: {successful} successful, {failed} failed")
        return successful, failed

    def close(self) -> None:
        """Clean up resources."""
        log.debug("DatabaseUploader closing...")
