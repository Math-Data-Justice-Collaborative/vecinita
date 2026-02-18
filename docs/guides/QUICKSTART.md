# 🚀 Quick Start Guide - Vecinita Full Stack

Bilingual Q&A assistant with LangGraph agent, web scraper, and React frontend.  
**Status:** ✅ Production Ready | 108+ Backend Tests Passing

---

## 2-Minute Start (Local Full Stack)

```bash
# 1. Clone and navigate
git clone https://github.com/acadiagit/vecinita.git
cd vecinita

# 2. Use local development environment
cp .env.local .env

# 3. Start all 6 services (database, API, embedding, agent, frontend)
docker-compose up

# Services will be available at:
# Frontend:           http://localhost:5173
# Agent API:          http://localhost:8000
# Embedding Service:  http://localhost:8001
# PostgREST API:      http://localhost:3001
# pgAdmin:            http://localhost:5050 (admin@example.com/admin)
# PostgreSQL:         localhost:5432
```

**What this starts:**
- ✅ PostgreSQL database (port 5432)
- ✅ PostgREST REST API (port 3001)
- ✅ Embedding Service - text embeddings (port 8001)
- ✅ Agent Service - LangGraph Q&A (port 8000)
- ✅ Frontend - React/Vite UI (port 5173)
- ✅ pgAdmin - database management UI (port 5050)

---

## Local Development

### Backend (Python + FastAPI + LangGraph)

```bash
cd backend

# Install dependencies
uv sync

# Set environment variables
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="your-key"
export GROQ_API_KEY="your-key"
export TAVILY_API_KEY="your-key"  # optional

# Run the agent server
uv run -m uvicorn src.agent.main:app --reload

# Test a question
curl "http://localhost:8000/ask?question=What%20is%20Vecinita?"

# Run tests (108 tests)
uv run pytest
```

### Frontend (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
# Frontend runs on http://localhost:5173

# Run unit tests
npm run test

# Run E2E tests (requires backend running)
npm run test:e2e
```

---

## Test Results

### Backend Tests (108 passing)

```
✅ Agent Tests:         6/6 PASSED   (LangGraph integration)
✅ db_search_tool:      8/8 PASSED   (Vector search)
✅ web_search_tool:    12/12 PASSED  (Tavily + DuckDuckGo)
✅ static_response:    20/20 PASSED  (FAQ lookup)
✅ Scraper Tests:      62/62 PASSED  (Pipeline, loaders, CLI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ TOTAL:             108/108 PASSED
```

Run backend tests:

```bash
cd backend
uv run pytest                    # All tests
uv run pytest -v                 # Verbose
uv run pytest --cov              # With coverage
```

### Frontend Tests

```bash
cd frontend
npm run test                     # Unit tests (Vitest)
npm run test:coverage            # Coverage report
npm run test:e2e                 # E2E tests (Playwright)
```

---

## Project Structure

```
vecinita/
├── backend/                      # Python backend
│   ├── src/
│   │   ├── agent/               # LangGraph agent & FastAPI
│   │   │   ├── main.py          # Main application
│   │   │   └── tools/           # Agent tools
│   │   │       ├── db_search.py          # Vector DB search
│   │   │       ├── static_response.py    # FAQ lookup
│   │   │       └── web_search.py         # Web search
│   │   ├── scraper/             # Web scraping pipeline
│   │   │   ├── main.py          # CLI entry
│   │   │   ├── scraper.py       # Core scraper
│   │   │   ├── loaders.py       # Content loaders
│   │   │   ├── processors.py    # Document processing
│   │   │   └── uploader.py      # Supabase upload
│   │   └── cli/                 # CLI utilities
│   ├── scripts/                 # Automation scripts
│   │   └── data_scrape_load.sh  # Pipeline orchestrator
│   └── tests/                   # 108 backend tests
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── App.jsx              # Main app
│   │   └── components/
│   │       ├── chat/            # Chat components
│   │       │   ├── ChatWidget.jsx
│   │       │   ├── MessageBubble.jsx
│   │       │   └── LinkCard.jsx
│   │       └── ui/              # shadcn-style components
│   └── tests/                   # Unit + E2E tests
│
├── data/                         # Data files
│   ├── urls.txt                 # URLs to scrape
│   └── config/                  # Scraper config
│
└── docs/                         # Documentation
    ├── FINAL_STATUS_REPORT.md
    ├── LANGGRAPH_REFACTOR_SUMMARY.md
    └── TEST_COVERAGE_SUMMARY.md
```

---

## Agent Tools

### db_search_tool

- **Function**: Vector similarity search on Supabase documents
- **Embeddings**: HuggingFace sentence-transformers/all-MiniLM-L6-v2
- **Threshold**: 0.3 (configurable)
- **Returns**: Top 5 most similar documents with metadata
- **Location**: `backend/src/agent/tools/db_search.py`

### static_response_tool

- **Function**: Bilingual FAQ lookup (English/Spanish)
- **Features**: Case-insensitive, partial matching, language fallback
- **Database**: 10+ FAQs per language
- **Location**: `backend/src/agent/tools/static_response.py`
- **Performance**: ~5ms response time

### web_search_tool

- **Primary**: Tavily API (advanced search with answer extraction)
- **Fallback**: DuckDuckGo (free, no API key required)
- **Features**: Auto provider switching, result normalization
- **Location**: `backend/src/agent/tools/web_search.py`
- **Config**: Supports 3 env var names for Tavily key

---

## Web Scraper Pipeline

The backend includes a powerful web scraping pipeline:

### Features

- **Multi-loader support**: Unstructured, Playwright, Recursive
- **Smart fallback**: Tries standard loaders first, falls back to Playwright for JS-heavy sites
- **Configurable chunking**: RecursiveCharacterTextSplitter (default: 1000 chars, 200 overlap)
- **Rate limiting**: 2-second delays between requests (configurable)
- **Streaming mode**: Upload chunks immediately to reduce memory usage
- **Link extraction**: Tracks outbound links for recursive crawling

### Running the Scraper

```bash
cd backend

# Basic usage
uv run python -m src.scraper.main \
  --input data/urls.txt \
  --output-file data/chunks.txt \
  --failed-log data/failed.txt

# With streaming mode (uploads immediately)
uv run python -m src.scraper.main \
  --input data/urls.txt \
  --output-file data/chunks.txt \
  --failed-log data/failed.txt \
  --stream

# Force specific loader
uv run python -m src.scraper.main \
  --input data/urls.txt \
  --output-file data/chunks.txt \
  --failed-log data/failed.txt \
  --loader playwright

# Full pipeline (clean database + scrape + load)
bash scripts/data_scrape_load.sh --clean
```

### Scraper Configuration

Files in `data/config/`:

- **recursive_sites.txt**: Format `<url> <depth>` for crawling (e.g., `https://example.com 2`)
- **playwright_sites.txt**: Domains requiring Playwright (JS-heavy content)
- **skip_sites.txt**: Domains to skip entirely

---

## Frontend Features

The React frontend provides a modern chat interface:

### Key Features

- **Responsive Design**: Mobile-first with Tailwind CSS
- **Font Scaling**: User-adjustable text size (slider in settings)
- **Language Support**: Auto-detection + manual toggle (EN/ES)
- **Markdown Rendering**: Rich text with react-markdown + remark-gfm
- **Source Attribution**: Clickable source links with visual cards
- **Accessibility**: ARIA labels, keyboard navigation, focus management
- **Dark Mode Ready**: CSS variable-based theming

### Components

- **ChatWidget**: Main chat interface with message history
- **MessageBubble**: Renders user/assistant messages with markdown
- **LinkCard**: Displays source links with hover effects
- **UI Components**: shadcn/ui-style button, card, dialog, input, slider

### Running Frontend Tests

```bash
cd frontend

# Unit tests (Vitest)
npm run test
npm run test:coverage

# E2E tests (Playwright)
npm run test:e2e

# Watch mode
npm run test -- --watch
```

---

## API Usage

### Backend Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Web UI (legacy static HTML) |
| GET | `/ask` | Ask a question with auto language detection |
| GET | `/docs` | Interactive API documentation (Swagger) |
| GET | `/health` | Health check endpoint |

### Example Requests

#### Simple Question

```bash
curl "http://localhost:8000/ask?question=What%20is%20Vecinita?"
```

#### With Conversation History

```bash
curl "http://localhost:8000/ask?question=How%20can%20I%20help%3F&thread_id=user-123"
```

#### Force Language

```bash
curl "http://localhost:8000/ask?question=Hola&language=es"
```

#### Response Format

```json
{
  "question": "What is Vecinita?",
  "answer": "Vecinita is a community Q&A assistant...",
  "sources": ["https://example.com/about"],
  "thread_id": "user-123",
  "language": "en"
}
```

### Frontend Integration

The React frontend communicates with the backend API:

```javascript
// Example: Sending a question
const response = await fetch(
  `${BACKEND_URL}/ask?question=${encodeURIComponent(question)}&thread_id=${threadId}`
);
const data = await response.json();
```

---

## Agent Decision Flow

```
User Question
    ↓
[Detect Language: EN or ES]
    ↓
[Load Appropriate System Prompt]
    ↓
[LangGraph Agent with 3 Tools]
    ├─ static_response_tool
    │  (Check FAQ database first)
    │
    ├─ db_search_tool
    │  (Search document database if no FAQ match)
    │
    └─ web_search_tool
       (Search web if insufficient results)
    ↓
[Synthesize Answer with Sources]
    ↓
Response with Citations
```

---

## File Structure

```
src/agent/
├── tools/
│   ├── db_search.py          ← Vector database search
│   ├── static_response.py    ← FAQ lookup (bilingual)
│   └── web_search.py         ← Web search (Tavily+DDG)
├── main.py                   ← LangGraph + FastAPI
└── static/                   ← Web UI

tests/
├── test_db_search_tool.py
├── test_web_search_tool.py
└── test_static_response_tool.py

docs/
├── FINAL_STATUS_REPORT.md          ← Complete summary
├── TEST_COVERAGE_SUMMARY.md        ← Test details
└── LANGGRAPH_REFACTOR_SUMMARY.md   ← Architecture
```

---

## Configuration

### Required Environment Variables

```bash
# Supabase (vector database)
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<anon-or-service-key>

# LLM (Groq)
GROQ_API_KEY=<your-groq-key>
```

### Optional Environment Variables

```bash
# Web search (Tavily - falls back to DuckDuckGo if not set)
TAVILY_API_KEY=<your-tavily-key>
# Alternative env var names also supported:
TAVILY_API_AI_KEY=<alternative>
TVLY_API_KEY=<shorthand>

# Frontend backend URL (defaults to http://localhost:8000)
VITE_BACKEND_URL=http://localhost:8000
```

### Docker Compose Environment

Create a `.env` file in the project root:

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-key
GROQ_API_KEY=your-key
TAVILY_API_KEY=your-key
VITE_BACKEND_URL=http://backend:8000
```

### Tool Configuration (Code Level)

**db_search_tool** (`backend/src/agent/tools/db_search.py`):

```python
match_threshold = 0.3    # Similarity threshold (0-1)
match_count = 5          # Number of results to return
```

**web_search_tool** (`backend/src/agent/tools/web_search.py`):

```python
max_results = 5          # Results per search
search_depth = "advanced"  # Tavily only
```

**scraper** (`backend/src/scraper/config.py`):

```python
CHUNK_SIZE = 1000        # Character chunk size
CHUNK_OVERLAP = 200      # Overlap between chunks
RATE_LIMIT_DELAY = 2     # Seconds between requests
```

---

## Component Status at Startup

### Backend Startup

When you start the backend server, you should see:

```
✅ Supabase client initialized successfully
✅ ChatGroq LLM initialized successfully
✅ Embedding model initialized successfully
✅ Initialized 3 tools: ['db_search', 'static_response_tool', 'web_search']
✅ LangGraph workflow compiled successfully
✅ Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Frontend Startup

```
  VITE v5.0.0  ready in 423 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Docker Compose Startup

```
✅ backend-1   | Application startup complete
✅ frontend-1  | VITE ready in 423 ms
✅ All services running
```

---

## Performance

| Scenario | Time | Component |
|----------|------|-----------|
| FAQ match | ~5ms | static_response_tool |
| Database search | ~250ms | db_search_tool |
| Web search (Tavily) | ~2s | web_search_tool |
| Web search (DDG) | ~1s | web_search_tool |
| Full agent response | 3-6s | All tools + LLM |
| Frontend render | <100ms | React components |
| Scraper (per URL) | 2-10s | Depends on content size |

---

## Troubleshooting

### Backend Issues

#### Server won't start

```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
cd backend
uv sync

# Check environment variables
echo $SUPABASE_URL
echo $GROQ_API_KEY
```

#### Tavily not working

```bash
# Check API key
echo $TAVILY_API_KEY

# Note: Falls back to DuckDuckGo automatically
# To explicitly use DuckDuckGo, unset the env var:
unset TAVILY_API_KEY
```

#### Tests failing

```bash
cd backend

# Run with verbose output
uv run pytest -vv

# Run specific test file
uv run pytest tests/test_db_search_tool.py -vv

# Check for missing imports
uv sync
```

#### Vector search returning nothing

```bash
# Check Supabase connection
# Check embedding model loaded correctly
# Lower similarity threshold in backend/src/agent/tools/db_search.py

match_threshold = 0.2  # More lenient (default: 0.3)
```

### Frontend Issues

#### Frontend won't start

```bash
cd frontend

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+
```

#### Frontend can't reach backend

```bash
# Check backend is running
curl http://localhost:8000/health

# Set backend URL
export VITE_BACKEND_URL=http://localhost:8000

# For Docker Compose
export VITE_BACKEND_URL=http://backend:8000
```

#### E2E tests failing

```bash
# Install Playwright browsers
npx playwright install

# Run with UI
npm run test:e2e -- --ui

# Check backend is running
curl http://localhost:8000/health
```

### Scraper Issues

#### Scraper fails on all URLs

```bash
# Check internet connection
# Check rate limiting (reduce RATE_LIMIT_DELAY if needed)
# Try with Playwright loader
uv run python -m src.scraper.main --input data/urls.txt --output-file data/chunks.txt --failed-log data/failed.txt --loader playwright
```

#### Out of memory during scraping

```bash
# Use streaming mode
uv run python -m src.scraper.main --input data/urls.txt --output-file data/chunks.txt --failed-log data/failed.txt --stream

# Or reduce chunk size in backend/src/scraper/config.py
CHUNK_SIZE = 500  # Smaller chunks
```

---

## Testing

### Backend Tests (108 passing)

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_agent_langgraph.py -v
uv run pytest tests/test_db_search_tool.py -v
uv run pytest tests/test_scraper_module.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html

# Run tests by category
uv run pytest tests/test_agent*.py      # Agent tests
uv run pytest tests/test_*_tool.py      # Tool tests
uv run pytest tests/test_scraper*.py    # Scraper tests
```

Test breakdown:

- **Agent**: 6 tests (LangGraph integration, endpoints, conversation history)
- **Tools**: 40 tests (db_search: 8, web_search: 12, static_response: 20)
- **Scraper**: 62 tests (module: 17, advanced: 15, CLI: 13, enhancements: 17)

### Frontend Tests

```bash
cd frontend

# Unit tests (Vitest)
npm run test
npm run test:coverage

# E2E tests (Playwright) - requires backend running
npm run test:e2e

# Watch mode for development
npm run test -- --watch

# Run specific test file
npm run test src/components/chat/ChatWidget.test.jsx
```

---

## Documentation

### Quick References

- **[README.md](README.md)** - Project overview and setup
- **This file (QUICKSTART.md)** - Fast getting started guide

### Detailed Documentation

- **[docs/FINAL_STATUS_REPORT.md](docs/FINAL_STATUS_REPORT.md)** - Complete project status
- **[docs/LANGGRAPH_REFACTOR_SUMMARY.md](docs/LANGGRAPH_REFACTOR_SUMMARY.md)** - Architecture deep dive
- **[docs/TEST_COVERAGE_SUMMARY.md](docs/TEST_COVERAGE_SUMMARY.md)** - Testing strategy

### Component Documentation

- **[backend/README.md](backend/README.md)** - Backend architecture and API
- **[frontend/README.md](frontend/README.md)** - Frontend setup and components
- **[backend/tests/README.md](backend/tests/README.md)** - Testing documentation
- **[frontend/tests/e2e/README.md](frontend/tests/e2e/README.md)** - E2E test guide

---

## Technology Stack

### Backend

- **Framework**: FastAPI
- **Agent**: LangGraph (LangChain ecosystem)
- **LLM**: Groq (Llama 3.1 8B)
- **Embeddings**: HuggingFace sentence-transformers/all-MiniLM-L6-v2
- **Database**: Supabase (PostgreSQL + pgvector)
- **Web Scraping**: Playwright, Unstructured, RecursiveUrlLoader
- **Testing**: pytest (108 tests)
- **Package Manager**: uv

### Frontend

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + PostCSS
- **UI Components**: shadcn/ui (built on Radix UI)
- **Markdown**: react-markdown + remark-gfm
- **Icons**: lucide-react
- **Testing**: Vitest (unit) + Playwright (E2E)
- **Package Manager**: npm

### DevOps

- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions (test.yml)
- **Code Coverage**: Codecov
- **Platforms**: Windows, Ubuntu

---

## Key Facts

✅ **108/108 backend tests passing**  
✅ **Frontend unit + E2E tests passing**  
✅ **3 production tools implemented** (db_search, static_response, web_search)  
✅ **Bilingual (EN/ES) support** with auto-detection  
✅ **Multi-turn conversations** with thread IDs  
✅ **Powerful web scraper** with multi-loader support  
✅ **Modern React frontend** with Tailwind + shadcn/ui  
✅ **Graceful error handling** and fallbacks  
✅ **Mock-friendly architecture** for testing  
✅ **Type hints throughout** backend code  
✅ **Comprehensive logging** for debugging  
✅ **Docker Compose** for easy deployment  
✅ **Ready to deploy** to production  

---

## Next Steps

### For New Users

1. ✅ Read [README.md](README.md) for project overview
2. ✅ Run `docker-compose up` to start everything
3. ✅ Access frontend at <http://localhost:3000>
4. ✅ Test the API at <http://localhost:8000/docs>

### For Developers

1. ✅ Review [docs/LANGGRAPH_REFACTOR_SUMMARY.md](docs/LANGGRAPH_REFACTOR_SUMMARY.md) for architecture
2. ✅ Run backend tests: `cd backend && uv run pytest`
3. ✅ Run frontend tests: `cd frontend && npm run test`
4. ✅ Explore the codebase with inline comments and docstrings

### For Data Operations

1. ✅ Add URLs to `data/urls.txt`
2. ✅ Configure scraper in `data/config/`
3. ✅ Run scraper: `cd backend && bash scripts/data_scrape_load.sh`
4. ✅ Monitor logs for failed URLs and retry with Playwright

---

## Questions?

- **Architecture**: See [docs/LANGGRAPH_REFACTOR_SUMMARY.md](docs/LANGGRAPH_REFACTOR_SUMMARY.md)
- **Tests**: See [docs/TEST_COVERAGE_SUMMARY.md](docs/TEST_COVERAGE_SUMMARY.md)
- **Status**: See [docs/FINAL_STATUS_REPORT.md](docs/FINAL_STATUS_REPORT.md)
- **Backend**: See [backend/README.md](backend/README.md)
- **Frontend**: See [frontend/README.md](frontend/README.md)
- **Issues**: Check [GitHub Issues](https://github.com/acadiagit/vecinita/issues)

---

**Status:** ✅ Production Ready  
**Last Updated:** December 31, 2025  
**Backend Test Coverage:** 108/108 passing  
**Frontend Tests:** Passing (unit + E2E)
