"""
Utils Module - Centralized Utilities Inventory

This document tracks all utilities in backend/src/utils/ and their usage patterns.
"""

# ============================================================================
# UTILITIES INVENTORY
# ============================================================================

## FAQ Loader (`faq_loader.py`)

- **Purpose**: Load FAQs from markdown files with in-memory caching
- **Exports**:
  - `load_faqs_from_markdown(lang: str) -> Dict[str, str]`
  - `reload_faqs(lang: Optional[str]) -> None`
  - `get_faq_stats() -> Dict[str, int]`
- **Used By**:
  - `backend/src/services/agent/tools/static_response.py` (main consumer)
  - `backend/tests/test_*` (test files)
- **Configuration**:
  - `FAQ_DIR` env var: Override FAQ directory (optional)
  - Default: `backend/src/services/agent/data/faqs/`
- **Features**:
  - 5-minute TTL cache with auto-reload
  - Markdown parsing (## Question\n\nAnswer format)
  - Punctuation-insensitive matching
  - Language fallback to English if not found

## HTML Cleaner (`html_cleaner.py`)

- **Purpose**: Remove boilerplate HTML (headers, footers, nav) and extract main content
- **Exports**:
  - `HTMLCleaner.clean_html(html: str, extract_main: bool = True) -> str`
  - `HTMLCleaner.clean_html_to_text(html: str) -> str`
  - `HTMLCleaner.is_boilerplate_element(element) -> bool`
- **Used By**:
  - `backend/src/services/scraper/loaders.py` (HTML scraping cleanup)
  - `backend/src/services/scraper/processors.py` (text post-processing)
  - `backend/tests/test_html_cleaner.py` (unit tests)
- **Features**:
  - Removes 50+ boilerplate class/ID patterns
  - Extracts main content container priority (main → article → div.content)
  - Removes common footer text patterns (privacy, cookies, etc.)
  - BeautifulSoup-based parsing
- **Configuration**: None (stateless)

## Supabase Embeddings (`supabase_embeddings.py`)

- **Purpose**: LangChain-compatible wrapper for Supabase Edge Functions embedding service
- **Exports**:
  - `SupabaseEmbeddings` class
- **Used By**:
  - `backend/src/services/agent/server.py` (embeddings initialization)
  - `backend/src/services/scraper/uploader.py` (optional remote embeddings)
- **Features**:
  - Calls Supabase Edge Function via HTTP
  - Batch embedding support
  - Compatible with LangChain embedding interface
- **Configuration**:
  - `SUPABASE_URL`: Supabase project URL
  - `SUPABASE_KEY`: Service role key

# ============================================================================
# EXTRACTED UTILITIES (Phase 2)
# ============================================================================

## Extraction Summary

**Moved in Phase 2 (from src/services/agent/utils/ to src/utils/):**
1. ✅ `markdown_faq_loader.py` → `faq_loader.py`
2. ✅ `html_cleaner.py` → Copied to src/utils/ (also kept in agent/utils for now)

**Import Updates:**
- ✅ `static_response.py`: Now imports from `src.utils` instead of `..utils`
- ✅ `test_html_cleaner.py`: Updated to import from `src.utils`

**Versioning:** Module paths are backward-compatible; old imports may still work if agent/utils versions kept.

# ============================================================================
# UTILITY USAGE MATRIX
# ============================================================================

| Utility | FAQ Loader | HTML Cleaner | Supabase Embeddings |
|---------|-----------|--------------|-------------------|
| Agent Tools | ✅ static_response.py | ❌ | ✅ server.py |
| Scraper | ❌ | ✅ loaders.py | ✅ uploader.py |
| API Gateway | ❌ | ❌ | ❌ |
| Embeddings Service | ❌ | ❌ | ✅ client.py |

# ============================================================================
# FUTURE CONSOLIDATION OPPORTUNITIES (Phase 2B)
# ============================================================================

## Vector Uploader (`vector_uploader.py`) - PLANNED

**Consolidates:**
- `backend/src/services/agent/utils/vector_loader.py` (currently 582 lines)
- `backend/src/services/scraper/uploader.py` (currently 425 lines)

**Benefits:**
- Single source of truth for embedding upload logic
- Unified embedding fallback chain (Service → FastEmbed → HuggingFace)
- Reduced code duplication (~200 lines)

**Planned Exports:**
- `DocumentUploader` class
- `upload_with_embeddings(): Uploads using Embedding Service`
- `upload_with_fallback(): Uploads with automatic fallback chain`

**Implementation Plan:**
- Create `src/utils/vector_uploader.py`
- Update `services/scraper/uploader.py` to wrap the utility
- Update `services/agent/utils/vector_loader.py` to import from utility
- Keep both original locations for backward compatibility

## Note

This consolidation was identified in Phase 2 planning but deferred to Phase 2B due to scope.
Currently, both modules work independently. Consolidation would add ~1 hour of refactoring
but reduce maintenance burden long-term.

# ============================================================================
# SHARED UTILITIES RECOMMENDATIONS
# ============================================================================

### Consider Moving to src/utils/ (Future Phases)

| Module | Location | Reusability | Consolidation Priority |
|--------|----------|-------------|----------------------|
| Text Sanitizer | scraper/utils.py | Medium | Low (scraper-specific) |
| Document Processor | scraper/processors.py | High | Medium (generic processor) |
| Database Uploader | scraper/uploader.py | High | **High (duplicate logic with vector_loader)** |

# ============================================================================
# DOCUMENTATION FOR DEVELOPERS
# ============================================================================

## Adding a New Utility

1. Create module in `backend/src/utils/module_name.py`
2. Add public exports to `src/utils/__init__.py`
3. Document usage in this README
4. Add unit tests in `tests/test_utils/test_module_name.py`
5. Update ARCHITECTURE documentation

## Migrating an Existing Utility

If moving a utility from `services/X/utils/` to `src/utils/`:

1. Create new module in `src/utils/`
2. Update all imports across codebase
3. Keep backward-compatible import in original location (optional, for gradual migration):
   ```python
   # backend/src/services/X/utils/old_module.py
   # Deprecated: Import from src.utils instead
   from src.utils import FunctionName
   ```
4. Mark original as deprecated in docstring
5. Update tests
6. Document in this file

## Testing Utilities

All utilities in `src/utils/` should have:
- Unit tests in `tests/test_utils/`
- No external service dependencies (mock if needed)
- Fast execution (<100ms per test)

Example:
```bash
pytest tests/test_utils/ -v
```
