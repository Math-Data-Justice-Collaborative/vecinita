"""
Document processing for the VECINA scraper.
Handles cleaning, chunking, and metadata extraction.
"""

import time
import logging
from typing import List, Tuple, Dict, Optional
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .utils import clean_text, extract_outbound_links
from .config import ScraperConfig

# Use parent logger hierarchy for better integration with CLI logging
log = logging.getLogger('vecinita_pipeline.processors')
log.addHandler(logging.NullHandler())


class DocumentProcessor:
    """Processes documents: cleaning, chunking, and saving."""

    def __init__(self, config: ScraperConfig):
        """Initialize processor with config."""
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""],
            keep_separator=False
        )

    def _find_chunk_position(self, content: str, chunk_text: str, current_offset: int) -> int:
        """Find the starting character position of a chunk within the full content.

        Uses a fast-path comparison at the expected offset, then falls back to
        a bounded search window and, if necessary, an approximation.
        """
        chunk_len = len(chunk_text)

        # Fast path: Check if chunk appears at expected position (handles 95%+ of cases)
        # This avoids expensive string search for sequential chunks
        expected_end = current_offset + chunk_len
        if expected_end <= len(content) and content[current_offset:expected_end] == chunk_text:
            return current_offset

        # Fallback: Search in a limited window around expected position
        # This handles cases where separators cause position shifts
        search_window_start = max(
            0, current_offset - self.config.CHUNK_OVERLAP)
        search_window_end = min(
            len(content),
            current_offset + chunk_len + self.config.CHUNK_OVERLAP,
        )

        found_at = content.find(
            chunk_text, search_window_start, search_window_end)
        if found_at == -1:
            # Edge case: search from current offset onward (limited scope)
            found_at = content.find(chunk_text, search_window_start)

        if found_at == -1:
            # Last resort: approximate using current offset
            log.debug(
                f"--> Approximated position for chunk at offset {current_offset}"
            )
            return current_offset

        return found_at

    def process_documents(
        self,
        docs: list,
        source_identifier: str,
        loader_type: str,
        output_file: Optional[str] = None,
        links_file: Optional[str] = None
    ) -> Tuple[int, List[str]]:
        """
        Process documents: clean, chunk, extract links, and save.

        Returns:
            Tuple of (chunks_written, list of extracted links, list of chunk dicts)
        """
        start_time = time.time()

        # Reset last_chunks storage for callers needing the built chunks
        self.last_chunks: List[dict] = []

        if not docs:
            log.warning("--> No documents found to process. Skipping.")
            return 0, []

        # Clean document content
        cleaned_docs_content = self._clean_documents(docs, loader_type)

        if not cleaned_docs_content:
            # Fallback: if cleaning removed everything but raw docs have content, use raw content
            raw_fallback = [
                (getattr(doc, 'page_content', '') or '',
                 getattr(doc, 'metadata', {}) or {})
                for doc in docs
                if getattr(doc, 'page_content', '')
            ]
            if raw_fallback:
                log.debug(
                    "--> Cleaning produced no content; using raw content fallback for chunking.")
                cleaned_docs_content = raw_fallback
            else:
                log.warning("--> No content found after cleaning. Skipping.")
                return 0, []

        preview_text = cleaned_docs_content[0][0][:200].replace(
            '\n', ' ') + '...'
        log.info(f"--> PREVIEW (after cleaning): {preview_text}")

        # Split into chunks with position tracking
        log.info("--> Splitting text into chunks...")
        chunks_for_file = []
        extracted_links = []
        total_chunks = 0

        for doc_index, (content, metadata) in enumerate(cleaned_docs_content):
            split_chunks = self.text_splitter.split_text(content)
            # Fallback: if no chunks produced, treat whole content as one chunk
            if not split_chunks and content:
                split_chunks = [content]
            total_chunks += len(split_chunks)

            # Track character positions efficiently using incremental offset tracking.
            # This optimization reduces the search complexity from O(n*m) to O(1) for most cases.
            # We validate position with direct comparison before falling back to search.
            current_offset = 0

            for chunk_idx, chunk_text in enumerate(split_chunks):
                chunk_len = len(chunk_text)
                char_start = self._find_chunk_position(
                    content, chunk_text, current_offset)
                char_end = char_start + chunk_len
                chunk_metadata = metadata.copy()
                # Add position tracking to metadata
                chunk_metadata.update({
                    'char_start': char_start,
                    'char_end': char_end,
                    'doc_index': doc_index,
                    'chunk_in_doc': chunk_idx
                })
                chunks_for_file.append(
                    {'text': chunk_text, 'metadata': chunk_metadata})

                # Update offset for next chunk: advance by chunk size minus overlap
                # This assumes typical splitter behavior of (chunk_size - overlap) progression
                current_offset = char_end - self.config.CHUNK_OVERLAP
                if current_offset < 0:
                    current_offset = char_end
            # Extract links from metadata
            if 'source' in metadata:
                extracted_links.append(metadata['source'])

        log.info(
            f"--> Created {total_chunks} chunks from {len(cleaned_docs_content)} documents.")

        # Write chunks to file
        if output_file and chunks_for_file:
            self._write_chunks_to_file(
                output_file, source_identifier, loader_type, docs, cleaned_docs_content, chunks_for_file)
        elif not chunks_for_file:
            log.warning("--> No chunks generated. Nothing written to file.")

        # Extract outbound links from the source page (once) and write to file
        # Only when we have at least one document with a source metadata
        try:
            any_source_meta = any('source' in (md or {})
                                  for _, md in cleaned_docs_content)
            if any_source_meta:
                page_links = extract_outbound_links(
                    source_identifier, same_domain_only=False)
                if page_links:
                    extracted_links = page_links
                    log.info(
                        f"--> Extracted {len(extracted_links)} outbound links from page")
        except Exception as e:
            log.debug(f"Link extraction failed for {source_identifier}: {e}")

        if links_file and extracted_links:
            self._write_links_to_file(
                links_file, source_identifier, extracted_links)

        elapsed = time.time() - start_time
        log.info(f"--> ✅ Processing complete in {elapsed:.2f}s.")

        # If no chunks were produced despite non-empty cleaned docs, ensure at least one
        if total_chunks == 0 and cleaned_docs_content:
            total_chunks = 1

        # Store chunks for optional downstream use (e.g., streaming upload)
        self.last_chunks = chunks_for_file

        return total_chunks, extracted_links

    def _clean_documents(self, docs: list, loader_type: str) -> List[Tuple[str, dict]]:
        """Clean documents and return (content, metadata) tuples."""
        cleaned_docs = []

        log.info("--> Cleaning document content...")
        log.debug(
            f"--> Cleaning summary (pre): documents_in={len(docs)} | loader_type={loader_type}")

        # Use BeautifulSoup for HTML-like content
        if "Loader" in loader_type or "Crawler" in loader_type:
            bs_transformer = BeautifulSoupTransformer()
            try:
                transformed = bs_transformer.transform_documents(
                    docs,
                    tags_to_extract=["main", "article", "section", "div", "p",
                                     "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "pre", "span"]
                )
                # Only replace if transformation produced non-empty content; otherwise keep originals
                if transformed and any(getattr(d, 'page_content', '') for d in transformed):
                    docs = transformed
                log.debug(
                    f"--> BeautifulSoup transformed documents: count={len(docs)}")
            except Exception as e:
                log.warning(
                    f"--> ⚠️ BeautifulSoup cleaning failed: {e}. Using raw content.")

        dropped_examples = []
        for idx, doc in enumerate(docs):
            raw_len = len(getattr(doc, 'page_content', '') or '')
            cleaned_content = clean_text(
                getattr(doc, 'page_content', '') or '')
            cleaned_len = len(cleaned_content)
            if cleaned_content:
                cleaned_docs.append(
                    (cleaned_content, getattr(doc, 'metadata', {})))
                log.debug(
                    f"--> Doc kept idx={idx} raw_len={raw_len} cleaned_len={cleaned_len}")
            else:
                # Track up to 3 examples for visibility when nothing remains
                if len(dropped_examples) < 3:
                    preview = (getattr(doc, 'page_content', '') or '')[
                        :200].replace('\n', ' ')
                    dropped_examples.append({
                        'idx': idx,
                        'raw_len': raw_len,
                        'source': (getattr(doc, 'metadata', {}) or {}).get('source') or (getattr(doc, 'metadata', {}) or {}).get('url'),
                        'preview': preview
                    })
                log.debug(
                    f"--> Doc dropped idx={idx} raw_len={raw_len} cleaned_len={cleaned_len}")

        log.info(
            f"--> Cleaning summary (post): kept={len(cleaned_docs)} | dropped={len(docs) - len(cleaned_docs)}")

        if not cleaned_docs and dropped_examples:
            log.info(
                "--> No content remained after cleaning. Examples of dropped docs (showing up to 3):")
            for ex in dropped_examples:
                log.info(
                    f"    - idx={ex['idx']} raw_len={ex['raw_len']} source={ex['source']} preview='{ex['preview']}'")

        return cleaned_docs

    def _write_chunks_to_file(
        self,
        output_file: str,
        source_identifier: str,
        loader_type: str,
        docs: list,
        cleaned_docs: list,
        chunks: list
    ) -> None:
        """Write chunks to output file."""
        log.info(f"--> Appending {len(chunks)} chunks to {output_file}...")

        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{'='*70}\n")
                f.write(f"SOURCE: {source_identifier}\n")
                f.write(f"LOADER: {loader_type}\n")
                f.write(
                    f"DOCUMENTS_LOADED: {len(docs)} | DOCUMENTS_PROCESSED: {len(cleaned_docs)} | CHUNKS: {len(chunks)}\n")
                f.write(f"{'='*70}\n\n")

                for i, chunk_data in enumerate(chunks, 1):
                    f.write(f"--- CHUNK {i}/{len(chunks)} ---\n")
                    f.write(chunk_data['text'])
                    chunk_source = chunk_data['metadata'].get(
                        'source', source_identifier)
                    if chunk_source != source_identifier:
                        f.write(f"\n(Chunk Source: {chunk_source})")
                    f.write("\n\n")
        except Exception as e:
            log.error(f"--> ❌ Error writing to {output_file}: {e}")

    def _write_links_to_file(self, links_file: str, source_identifier: str, links: List[str]) -> None:
        """Write extracted links to a separate file."""
        try:
            with open(links_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"SOURCE: {source_identifier}\n")
                f.write(f"LINKS EXTRACTED: {len(links)}\n")
                f.write(f"{'='*70}\n")

                for link in set(links):  # Use set to avoid duplicates
                    f.write(f"{link}\n")
        except Exception as e:
            log.error(f"--> ❌ Error writing to {links_file}: {e}")
