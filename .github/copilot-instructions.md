# Vecinita Copilot Instructions

Vecinita is a **RAG (Retrieval-Augmented Generation) Q&A Assistant** using LangChain, LangGraph, and Supabase. It scrapes web content, stores embeddings in a vector database, and answers user questions with source attribution.

## Multi-Repo Deployment Topology (Canonical)

Use this mapping as source-of-truth when implementing infra changes:

- **Chat Frontend** (`joseph-c-mcguire/Vecinitafrontend`) -> Render frontend
- **Data Management Frontend** (`Math-Data-Justice-Collaborative/vecinita-data-management-frontend`) -> Render frontend
- **Data Management API** (`Math-Data-Justice-Collaborative/vecinita-data-management`) -> Render private service in Virginia
- **Scraper** (`Math-Data-Justice-Collaborative/vecinita-scraper`) -> Modal deploy
- **Embedding Modal** (`Math-Data-Justice-Collaborative/vecinita-embedding`) -> Modal deploy
- **Model Modal** (`Math-Data-Justice-Collaborative/vecinita-model`) -> Modal deploy

### Network/Data Isolation Rules

- Data Management Frontend should call Data Management API directly.
- Data Management API must remain private (no public ingress) and restricted CORS allow-list.
- Agent/backend and Data Management API should call model/embedding/scraper via direct Modal endpoints.

### CI/CD Rule

- Service repositories own their own test/deploy workflows.
- Root repo orchestrates cross-repo release via `.github/workflows/multi-repo-release-orchestrator.yml`.
- Reusable dispatcher workflow is `.github/workflows/reusable-dispatch-repo-workflow.yml`.

### Copilot Guidance Artifacts

- Skill: `.github/skills/multi-repo-cicd-orchestration/SKILL.md`
- Skill: `.github/skills/modal-llm-agent-development/SKILL.md`
- Agent: `.github/agents/release-orchestrator.agent.md`
- Quality hook checklist: `.github/hooks/copilot-cicd-quality-hook.md`

## Architecture Overview

### Data Flow
1. **Web Scraping** ([../backend/src/scraper/main.py](../backend/src/scraper/main.py)): Scraper entrypoint and orchestration for ingestion jobs
2. **Vector Storage** ([../backend/src/agent/utils/vector_loader.py](../backend/src/agent/utils/vector_loader.py)): Chunk/embedding load path used by the agent stack
3. **Q&A Engine** ([../backend/src/agent/main.py](../backend/src/agent/main.py)): FastAPI app detects query language, retrieves similar docs, and returns sourced answers

### Key Components
- **FastAPI Server** (src/main.py): Two main endpoints—`GET /` (UI), `GET /ask` (Q&A logic)
- **Supabase PostgreSQL**: Stores document chunks with embeddings; RPC function `search_similar_documents` performs vector similarity search
- **LLM**: Groq's Llama 3.1 8B (configured via `GROQ_API_KEY`)
- **Embeddings**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (local, fast)
- **Web UI**: [../frontend/index.html](../frontend/index.html)—chat frontend entrypoint

## Data Pipeline & Configuration

### Orchestration Script
[../backend/scripts/data_scrape_load.sh](../backend/scripts/data_scrape_load.sh) automates the full pipeline:
- Accepts `--clean` flag to truncate database (additive mode is default)
- Runs scraper in two passes: standard loaders first, then Playwright for failures
- Loads chunks into Supabase with deduplication via `unique_content_source` constraint
- Restarts Docker container on completion

### Configuration Files (data/config/)
- **recursive_sites.txt**: Format `<url> <depth>` for crawling (e.g., `https://example.com 2`)
- **playwright_sites.txt**: Domains requiring Playwright (JS-heavy content)
- **skip_sites.txt**: Domains to skip entirely

### URL Input
[../data/urls.txt](../data/urls.txt): List of URLs to scrape (one per line, ignoring comments starting with `#`)

## Development Workflows

### UV Package Manager
This project uses **uv** for fast, reliable dependency management and script execution. Install it first:
```bash
# Install UV (https://docs.astral.sh/uv/getting-started/)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Running Locally
```bash
# Recommended: Sync dependencies and run with uv
uv sync
uv run -m uvicorn src.agent.main:app --reload

# Alternative: Direct uvicorn (ensure dependencies installed)
cd src && uvicorn main:app --reload
```

### Docker Development
```bash
docker-compose up      # Run with services
docker-compose up -d   # Background
docker-compose down    # Stop & remove containers
```

### Testing
```bash
# Recommended: Use uv to run tests with isolated dependencies
uv run pytest

# Run specific test file
uv run pytest tests/test_main.py

# Run with coverage
uv run pytest --cov

# Run marked tests (unit, integration, db, api, ui)
uv run pytest -m unit

# Install Playwright browsers (required for UI tests)
uv run playwright install
```

Fixtures in [../tests/conftest.py](../tests/conftest.py) provide mocked Supabase, embedding models, and LLM clients. See [../tests/README.md](../tests/README.md) for full test strategy.

## Language-Aware Prompting

The `/ask` endpoint uses `langdetect` to detect query language and selects the appropriate prompt template:
- **Spanish** (es): System prompt in Spanish with Spanish instructions
- **English** (default): System prompt in English

Both enforce:
1. Answer only from provided context
2. Cite sources with `(Fuente: URL)` or `(Source: URL)`
3. Return fallback message if no relevant docs found

See [../backend/src/agent/main.py](../backend/src/agent/main.py) for prompt templates and request handling.

## Key Patterns & Conventions

### Dependency Pinning (pyproject.toml)
- **onnxruntime & tokenizers**: Windows-specific versions (dev/RC releases lack wheels)
- **sentence-transformers & fastembed**: Pinned to avoid NumPy 2.x conflicts
- **LangSmith ≥0.4.56**: Compatible with NumPy 2.x for tracing

### Scraper Design
- **Rate limiting**: 2-second delays between requests (RATE_LIMIT_DELAY in scraper_to_text.py)
- **Loader selection**: Standard (Unstructured) first, fallback to Playwright for JS-heavy sites
- **Chunking**: RecursiveCharacterTextSplitter with configurable size (default 1000 chars, 200 overlap)
- **Failure recovery**: Failed URLs logged and re-run with Playwright in second pass

### Database Constraints
- **unique_content_source**: Prevents duplicate content; enables safe re-scraping
- **Vector search RPC**: `search_similar_documents(query_embedding, match_threshold, match_count)`—default threshold 0.3, return top 5

### Static File Mounting
FastAPI mounts `src/static/` directory; ensure `index.html` and `favicon.ico` exist for `/` and `/favicon.ico` endpoints.

## Environment Variables

Required in `.env`:
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<anon-or-service-key>
GROQ_API_KEY=<your-groq-api-key>
```

Optional: `DATABASE_URL` (for direct PostgreSQL operations)

## Error Handling & Debugging

- **Missing UI**: Check static path in error message; ensure `src/static/index.html` exists
- **Embedding failures**: Verify HuggingFace model download; model auto-caches on first use
- **Vector search failures**: Check Supabase RPC function exists and embedding dimensions match (384 for all-MiniLM-L6-v2)
- **Scraper timeouts**: Increase RATE_LIMIT_DELAY or configure Playwright in config
- **Duplicate detection**: Database constraint `unique_content_source` silently rejects duplicates; check logs for details

## Testing Guidance

- **Unit tests** (fast): Test utility functions without external services
- **Integration tests**: Mock Supabase; test vector search logic
- **DB tests** (skipped in CI): Require real Supabase credentials
- **UI tests** (Playwright): Require running FastAPI server; mark with `@pytest.mark.ui`

Use `env_vars` fixture to inject test credentials; mock `supabase_client`, `embedding_model`, `llm` for isolated testing.
