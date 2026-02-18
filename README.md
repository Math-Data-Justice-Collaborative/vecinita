# Vecinita

![Tests](https://github.com/acadiagit/vecinita/actions/workflows/test.yml/badge.svg)
![Codecov](https://codecov.io/gh/acadiagit/vecinita/branch/main/graph/badge.svg)
![Python Versions](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![OS: Windows](https://img.shields.io/badge/OS-Windows-success)
![OS: Ubuntu](https://img.shields.io/badge/OS-Ubuntu-success)

**Vecinita** is a bilingual (English/Spanish) community Q&A assistant powered by LangGraph, combining vector database search, FAQ lookup, and web search to provide accurate answers with source attribution.

## Architecture

Vecinita uses a **microservice architecture** with 3 independent services:

- **Embedding Service** (FastAPI): Generates text embeddings using sentence-transformers
- **Agent Service** (FastAPI + LangGraph): Intelligent Q&A with tool routing
- **Scraper Service** (Background cron): Web content ingestion pipeline
- **Frontend** (React + Vite): Modern responsive UI

All services communicate via HTTP and can be deployed on Render's free tier ($0/month).

## Project Structure

This is a monorepo with separate backend and frontend:

```
vecinita/
├── backend/                      # Python backend (FastAPI + LangGraph)
│   ├── src/
│   │   ├── agent/               # LangGraph agent & tools
│   │   │   ├── main.py          # FastAPI app with LangGraph
│   │   │   ├── static/          # Web UI (legacy)
│   │   │   └── tools/           # db_search, static_response, web_search
│   │   ├── scraper/             # Web scraping pipeline
│   │   │   ├── main.py          # CLI entry point
│   │   │   ├── scraper.py       # VecinaScraper class
│   │   │   ├── loaders.py       # Content loaders
│   │   │   ├── processors.py    # Document processing
│   │   │   └── uploader.py      # Supabase upload
│   │   └── cli/                 # CLI tools
│   ├── scripts/                 # Automation scripts
│   │   └── data_scrape_load.sh  # Data pipeline orchestrator
│   └── tests/                   # 108 backend tests (pytest)
│
├── frontend/                     # React frontend (Vite + Tailwind)
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   └── components/
│   │       ├── chat/            # ChatWidget, MessageBubble, LinkCard
│   │       └── ui/              # shadcn-style UI components
│   └── tests/                   # Unit tests (Vitest) + E2E (Playwright)
│
├── data/                         # URL lists and scraper config
│   ├── urls.txt                 # URLs to scrape
│   └── config/                  # Scraper configuration
│
├── docs/                         # Comprehensive documentation
│   ├── FINAL_STATUS_REPORT.md
│   ├── LANGGRAPH_REFACTOR_SUMMARY.md
│   └── TEST_COVERAGE_SUMMARY.md
│
└── docker-compose.yml           # Multi-container orchestration
```

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start both backend and frontend
docker-compose up

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend (Python)

```bash
cd backend

# Install dependencies with uv (recommended)
uv sync

# Set environment variables (recommended: use a .env file)
# 1) Copy .env.example to .env at the repo root
# 2) Fill in your local secrets
# .env is already ignored by .gitignore and should not be committed
cp ../.env.example ../.env  # or create manually

# Run the agent server
uv run -m uvicorn src.agent.main:app --reload

# Run tests (108 tests)
uv run pytest
```

#### Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# (Optional) Create a local env file for the frontend
# echo "VITE_BACKEND_URL=http://localhost:8000" > .env.local

# Run dev server
npm run dev

# Run tests
npm run test          # Unit tests (Vitest)
npm run test:e2e      # E2E tests (Playwright)
```

## Environment Variables

- Manage secrets locally using the `.env` file at the repo root.
- A sanitized example is provided: `.env.example`.
- Do not commit `.env` or any real secrets; `.gitignore` already excludes common env files.
- Frontend can use `.env.local` for values like `VITE_BACKEND_URL`.


## Core Features

### Backend

- **LangGraph Agent**: Intelligent tool routing with 3 specialized tools
  - `db_search`: Vector similarity search on Supabase documents
  - `static_response`: Bilingual FAQ lookup (English/Spanish)
  - `web_search`: Tavily API + DuckDuckGo fallback
- **Web Scraper**: Multi-loader pipeline (Unstructured, Playwright, Recursive)
  - Smart rate limiting and error handling
  - Configurable chunking and metadata extraction
  - Streaming upload mode for large datasets
- **Bilingual Support**: Auto language detection (English/Spanish)
- **Conversation History**: Multi-turn conversations with thread IDs

### Frontend

- **Modern React UI**: Built with Vite, Tailwind CSS, and shadcn/ui
- **Responsive Design**: Mobile-first with accessibility support
- **Font Scaling**: User-adjustable text size
- **Markdown Rendering**: Rich text formatting with react-markdown
- **Source Attribution**: Clickable source links with visual cards

## Testing

### Backend Tests (108 passing)

```bash
cd backend
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest --cov              # With coverage
```

Test coverage:

- Agent tools: 40 tests (db_search, static_response, web_search)
- Scraper pipeline: 68 tests (loaders, processors, CLI, advanced scenarios)

### Frontend Tests

```bash
cd frontend
npm run test                     # Unit tests (Vitest)
npm run test:coverage            # Coverage report
npm run test:e2e                 # E2E tests (Playwright)
```

## Documentation

### Getting Started
- **[QUICKSTART.md](docs/guides/QUICKSTART.md)** - Complete setup guide (Docker + Local development)
- **[backend/README.md](backend/README.md)** - Backend API and tools documentation
- **[frontend/README.md](frontend/README.md)** - Frontend components and testing

### Deployment
- **[docs/RENDER_DEPLOYMENT_THREE_SERVICES.md](docs/RENDER_DEPLOYMENT_THREE_SERVICES.md)** - Step-by-step Render deployment (free tier)
- **[docs/QUICK_REFERENCE_MICROSERVICE.md](docs/QUICK_REFERENCE_MICROSERVICE.md)** - Quick reference for microservice setup
- **[docs/ARCHITECTURE_MICROSERVICE.md](docs/ARCHITECTURE_MICROSERVICE.md)** - Detailed architecture documentation

### Technical Documentation
- **[docs/](docs/)** - Comprehensive technical docs
  - [FINAL_STATUS_REPORT.md](docs/FINAL_STATUS_REPORT.md) - Project status and achievements
  - [LANGGRAPH_REFACTOR_SUMMARY.md](docs/LANGGRAPH_REFACTOR_SUMMARY.md) - Agent architecture details
  - [TEST_COVERAGE_SUMMARY.md](docs/TEST_COVERAGE_SUMMARY.md) - Test suite overview
  - [STREAMING_UX_SUMMARY.md](docs/STREAMING_UX_SUMMARY.md) - Enhanced streaming features
  - [IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - Complete implementation overview

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Web UI (legacy) |
| GET | `/ask` | Ask a question with language detection |
| GET | `/docs` | Interactive API documentation (Swagger) |
| GET | `/health` | Health check |

### Example API Request

```bash
# Simple question
curl "http://localhost:8000/ask?question=What%20is%20Vecinita?"

# With conversation history
curl "http://localhost:8000/ask?question=Tell%20me%20more&thread_id=user-123"

# Force Spanish
curl "http://localhost:8000/ask?question=Hola&language=es"
```

## Data Pipeline

The scraper pipeline processes web content into vector embeddings:

```bash
cd backend

# Run full pipeline
bash scripts/data_scrape_load.sh

# Or run components separately
uv run python -m src.scraper.main --input data/urls.txt --output-file data/chunks.txt --failed-log data/failed.txt

# Streaming mode (immediate upload)
uv run python -m src.scraper.main --input data/urls.txt --output-file data/chunks.txt --failed-log data/failed.txt --stream
```

Configuration files:

- `data/urls.txt` - URLs to scrape
- `data/config/recursive_sites.txt` - Sites for recursive crawling
- `data/config/playwright_sites.txt` - JS-heavy sites requiring Playwright
- `data/config/skip_sites.txt` - Domains to skip

## Environment Variables

### Required

```bash
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<anon-or-service-key>
GROQ_API_KEY=<your-groq-api-key>
```

### Optional

```bash
TAVILY_API_KEY=<your-tavily-key>                          # For enhanced web search
VITE_BACKEND_URL=http://localhost:8000                    # Frontend backend URL (local)
EMBEDDING_SERVICE_URL=http://embedding-service:8001       # Embedding service URL (Docker)
# For Render deployment: https://vecinita-embedding.onrender.com
```

## Technology Stack

### Backend

- **Framework**: FastAPI
- **Agent**: LangGraph (LangChain)
- **LLM**: Groq (Llama 3.1 8B) / DeepSeek / OpenAI / Ollama
- **Embeddings**: Microservice (sentence-transformers/all-MiniLM-L6-v2) with fallback chain
- **Database**: Supabase (PostgreSQL + pgvector)
- **Scraping**: Playwright, Unstructured, RecursiveUrlLoader
- **Testing**: pytest (108 tests)
- **Package Manager**: uv
- **Architecture**: Microservices (3 services: embedding, agent, scraper)

### Frontend

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Markdown**: react-markdown + remark-gfm
- **Testing**: Vitest (unit) + Playwright (E2E)
- **Package Manager**: npm

## Contributing

1. Create a feature branch from `main`
2. Make changes with tests
3. Run test suites: `cd backend && uv run pytest` and `cd frontend && npm run test`
4. Submit PR with clear description

## License

See [LICENSE](LICENSE) file for details.
