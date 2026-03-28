# VECINA Reorganized Code Structure

## Overview

The codebase has been reorganized into three distinct modules for clear separation of concerns:

```
src/
├── scraper/          (Data Scraping Backend)
├── agent/            (LLM/Agent Deployment - RAG Q&A Frontend)
└── cli/              (CLI Orchestrator)
```

---

## 1. **src/scraper/** - Data Scraping Backend (999 lines)

**Purpose**: Isolated web scraping and data extraction module for content harvesting.

**Modules**:
- `__init__.py` (10 lines) - Package initialization
- `config.py` (90 lines) - ScraperConfig, site categorization, configuration management
- `loaders.py` (197 lines) - SmartLoader for intelligent content loading (Recursive, Playwright, Unstructured)
- `processors.py` (171 lines) - DocumentProcessor for HTML cleaning, text chunking, metadata extraction
- `scraper.py` (207 lines) - VecinaScraper main orchestrator with enhanced logging
- `utils.py` (110 lines) - Utility functions (URL handling, text cleaning, file I/O)
- `link_tracker.py` (70 lines) - LinkTracker for hyperlink extraction and tracking
- `main.py` (144 lines) - CLI entry point for standalone scraper execution

**Key Characteristics**:
- Self-contained module with only internal relative imports
- No external dependencies on agent or CLI modules
- Can be used independently: `python -m src.scraper.main`
- Enhanced logging with logger hierarchy: `vecinita_pipeline.scraper`, `.loaders`, `.processors`

**Import Pattern**:
```python
from src.scraper.scraper import VecinaScraper
from src.scraper.config import ScraperConfig
from src.scraper.loaders import SmartLoader
# etc.
```

---

## 2. **src/agent/** - LLM/Agent Deployment (RAG Q&A System)

**Purpose**: FastAPI application serving the RAG Q&A assistant with language-aware prompting.

**Structure**:
```
src/agent/
├── main.py              - FastAPI app composition, shared runtime state, helper logic
├── routers/             - Endpoint modules grouped by concern
│   ├── ask.py           - /ask and /ask-stream handlers
│   ├── config.py        - /config and /model-selection handlers
│   ├── diagnostics.py   - /db-info and /test-db-search handlers
│   └── system.py        - /, /health, and /privacy handlers
├── static/              - Web UI assets
│   ├── index.html       - Interactive Q&A interface
│   ├── img/             - Images and icons
│   └── favicon.ico
└── utils/               - Agent support utilities
    ├── vector_loader.py (581 lines) - Embedding generation, vector DB operations
    ├── db_cli.py        (422 lines) - Database CLI operations
    ├── faq_loader.py    (97 lines) - FAQ data loading
    ├── load_faq.py      (98 lines) - FAQ script
    ├── supabase_db_test.py (49 lines) - Database testing
    ├── html_cleaner.py  (293 lines) - Legacy HTML cleaning (deprecated)
    └── scraper_to_text.py (737 lines) - Legacy monolithic scraper (deprecated)
```

**Key Characteristics**:
- FastAPI server for Q&A endpoint (`GET /ask`)
- Router-based HTTP surface while preserving `src.agent.main:app` as the stable entrypoint
- Language detection (Spanish/English) for query processing
- Vector search with Supabase PostgreSQL
- Local-only Ollama-backed LLM integration
- HuggingFace embeddings (local)
- Source attribution in responses
- CORS-enabled for cross-origin requests

**Main Endpoints**:
- `GET /` - Serves UI (index.html)
- `GET /ask` - Q&A query endpoint with language-aware prompting
- `GET /static/*` - Static file serving

**Legacy Files** (in utils/, not used by new scraper):
- `html_cleaner.py` - Only used by deprecated `scraper_to_text.py`
- `scraper_to_text.py` - Old monolithic scraper (replaced by new modular src/scraper/)

**Starting the Agent**:
```bash
uvicorn src.agent.main:app --reload
# or
python -m uvicorn src.agent.main:app --reload
```

---

## 3. **src/cli/** - CLI Orchestrator

**Purpose**: Command-line interface for the complete data scraping pipeline.

**Structure**:
```
src/cli/
├── __init__.py          - Package marker
├── __main__.py          - Enables: python -m src.cli
└── data_scrape_load.py (764 lines) - Main pipeline orchestrator
```

**Key Features**:
- Orchestrates full data pipeline: scrape → process → load to database
- Direct VecinaScraper execution (no subprocess) for enhanced logging
- Enhanced logging with color output and real-time progress
- Supports multiple flags: `--clean`, `--verbose`, `--stream`, `--debug`
- Docker container management with Python SDK
- Conditional file output based on `--debug` flag
- Deduplication and error recovery with Playwright re-run

**Scraper Import**:
```python
from src.scraper.scraper import VecinaScraper
```

**Usage**:
```bash
python -m src.cli --clean --stream
python -m src.cli --verbose
python -m src.cli --debug  # Creates local chunk file
```

**Entry Point** (via pyproject.toml):
```bash
vecinita-scrape --clean --stream
```

---

## Import Path Updates

All imports have been updated from `src.utils.scraper` to `src.scraper`:

**Before**:
```python
from src.utils.scraper.scraper import VecinaScraper
from src.utils.scraper.config import ScraperConfig
```

**After**:
```python
from src.scraper.scraper import VecinaScraper
from src.scraper.config import ScraperConfig
```

**Files Updated**:
- `src/cli/data_scrape_load.py` - 2 import statements
- `tests/test_scraper_module.py` - All scraper imports
- `tests/test_scraper_cli.py` - CLI scraper imports
- All documentation files in `docs/`

---

## Module Dependencies

```
┌─────────────────────────────────────────────────────┐
│          src/cli/data_scrape_load.py                │
│         (CLI Pipeline Orchestrator)                 │
│  Flags: --clean, --verbose, --stream, --debug       │
└──────────────────┬──────────────────────────────────┘
                   │
          ┌────────▼────────┐
          │ src/scraper/    │
          │ (Backend)       │
          │ 999 lines       │
          └─────────────────┘
                   │
          ┌────────▼────────────────────┐
          │ src/agent/utils/            │
          │ vector_loader.py            │
          │ db_cli.py                   │
          │ (Database Operations)       │
          └────────┬────────────────────┘
                   │
          ┌────────▼─────────────────┐
          │ Supabase PostgreSQL      │
          │ (Vector DB + Chunks)     │
          └──────────────────────────┘
                   │
┌──────────────────▼──────────────────┐
│   src/agent/main.py                 │
│   (FastAPI RAG Q&A Server)          │
│   Language-aware prompting          │
│   Vector search + LLM responses     │
└─────────────────────────────────────┘
```

---

## Initialization Steps

### Full Pipeline (Data Collection → Agent Deployment)

1. **Scrape Content**:
   ```bash
   python -m src.cli --clean --stream
   ```
   - Uses `src/scraper/` modules
   - Loads to Supabase via `src/agent/utils/vector_loader.py`

2. **Start Agent Server**:
   ```bash
   uvicorn src.agent.main:app --reload
   ```
   - Serves Q&A at `http://localhost:8000`
   - UI at `http://localhost:8000/` (from src/agent/static/index.html)

### Standalone Scraper

```bash
python -m src.scraper.main --urls data/urls.txt --output data/chunks.txt
```

### Docker Development

```bash
docker-compose up
# Runs both scraper pipeline and agent server
```

---

## Configuration

**Environment Variables** (.env):
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<anon-or-service-key>
GROQ_API_KEY=<your-groq-api-key>
```

**Scraper Configuration** (data/config/):
- `recursive_sites.txt` - URLs for recursive crawling (format: `<url> <depth>`)
- `playwright_sites.txt` - Domains requiring Playwright (JS-heavy)
- `skip_sites.txt` - Domains to skip

**URL List** (data/urls.txt):
- One URL per line
- Lines starting with `#` are comments and ignored

---

## Testing

**Run All Tests**:
```bash
uv run pytest
```

**Run Scraper Tests**:
```bash
uv run pytest tests/test_scraper_module.py -v
```

**Run CLI Tests**:
```bash
uv run pytest tests/test_scraper_cli.py -v
```

**Run with Coverage**:
```bash
uv run pytest --cov
```

---

## Benefits of This Organization

1. **Clear Separation of Concerns**:
   - `src/scraper/` - Data extraction only
   - `src/agent/` - LLM/RAG Q&A only
   - `src/cli/` - Orchestration only

2. **Modularity**:
   - Scraper can be used independently
   - Agent can use data from any source
   - CLI can orchestrate other modules

3. **Maintainability**:
   - Each module has single responsibility
   - Easier to debug and test
   - Clear dependency flow

4. **Scalability**:
   - Scraper can run on separate machine/schedule
   - Agent can scale independently
   - CLI can orchestrate multiple workers

5. **Import Clarity**:
   - `from src.scraper.*` - Always scraping backend
   - `from src.agent.*` - Always agent/LLM code
   - `from src.cli.*` - Always orchestration code

---

## Migration Notes

- **Removed**: `src/utils/scraper/` (merged into `src/scraper/`)
- **Moved**: `src/main.py` → `src/agent/main.py`
- **Moved**: `src/static/` → `src/agent/static/`
- **Moved**: `src/utils/*` → `src/agent/utils/`
- **Deprecated** (still in src/agent/utils/): `scraper_to_text.py`, `html_cleaner.py`

All import statements have been automatically updated.

---

## Summary

The reorganized structure provides:
- ✅ Clear module separation
- ✅ Independent scalability
- ✅ Easy to understand dataflow
- ✅ All scraper backend in one place (src/scraper/)
- ✅ All agent/LLM code together (src/agent/)
- ✅ CLI orchestration layer (src/cli/)
