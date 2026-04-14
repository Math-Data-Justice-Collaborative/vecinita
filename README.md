# Vecinita

![Tests](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/workflows/test.yml/badge.svg)
![Backend Coverage](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/workflows/backend-coverage.yml/badge.svg)
![Frontend Coverage](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/workflows/frontend-coverage.yml/badge.svg)
![Render](https://img.shields.io/badge/Render-Blueprint%20Ready-46E3B7?logo=render&logoColor=white)
![Python](https://img.shields.io/badge/python-3.10-blue)
![OS](https://img.shields.io/badge/OS-Ubuntu%2022.04-success)

**Vecinita** is a bilingual (English/Spanish) community Q&A assistant powered by LangGraph, combining vector database search, FAQ lookup, and web search to provide accurate answers with source attribution.

## Architecture

Vecinita uses a **microservice architecture** with agent, gateway, model, embedding, scraper, and frontend services:

- **Gateway Service** (FastAPI): Stable `/api/v1` surface for web clients
- **Agent Service** (FastAPI + LangGraph): Q&A orchestration and retrieval flow
- **Modal Routing Service** (FastAPI): Auth and routing hub for model/embedding/scraper traffic
- **Model Service** (FastAPI + Ollama/Modal): Chat generation endpoints
- **Embedding Service** (FastAPI): Text embedding generation endpoints
- **Scraper Service** (FastAPI + jobs): Ingestion and reindex triggers
- **Frontends** (React + Vite): Chat app and data-management app

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
│   │   │   └── uploader.py      # PostgreSQL load
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

### Recommended Root Workflow

From the repository root, use the Makefile as the default entry point for local development and verification:

```bash
make dev
make lint
make typecheck
make test-unit
```

Additional common targets:

```bash
make dev-attach
make dev-stop
make test-integration
make test-e2e
make docs-serve
```

### Prerequisites (Local)

Use these versions (or newer compatible versions):

- Python 3.10+
- `uv` (Python package manager used by this repo)
- Node.js 20+ and `npm` (frontend)

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install Node.js via `nvm` (recommended):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm install --lts
```

### Option 1: Docker Compose (Recommended)

```bash
# Start the standard local stack
docker compose up -d

# Access the application
# Frontend: http://localhost:5173
# Gateway API: http://localhost:8004/api/v1
# Agent API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

For the routing-centric microservices stack, use:

```bash
make microservices-up
make test-microservices-contracts
```

### Option 2: Local Development

#### Full stack with cascading logs (single terminal)

From repo root:

```bash
make dev
```

This starts embedding service, agent service, API gateway, and frontend in one terminal with merged cascading logs prefixed by service name.

Press `Ctrl+C` to stop all services cleanly.

```bash
make dev-stop     # Stop managed processes
make dev-tmux     # Optional legacy tmux split-pane session
make dev-attach   # Attach to tmux session started by make dev-tmux
```

Compatibility note: `./dev-session.sh` remains available as a root wrapper shim.

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

If your local `.env` contains empty values, tests may still fail provider checks. Ensure at least one LLM provider is configured for runtime paths:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3
# or
DEEPSEEK_API_KEY=...
# or
OPENAI_API_KEY=...
```

When using Ollama, `OLLAMA_MODEL` defaults to **`gemma3`** in code and templates if unset (see root `.env.example`).

#### Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# (Optional) Create a local env file for the frontend
# echo "VITE_GATEWAY_URL=http://localhost:8004/api/v1" > .env.local

# Run dev server
npm run dev

# Run tests
npm run test:unit     # Unit tests (Vitest)
npm run test:e2e      # E2E tests (Playwright)
```

From the repo root, the equivalent shortcuts are:

```bash
make dev-frontend
make lint-frontend
make typecheck-frontend
make test-frontend-unit
make test-frontend-e2e
```

## Environment Variables

- Manage secrets locally using the `.env` file at the repo root.
- A sanitized example is provided: `.env.example`.
- Do not commit `.env` or any real secrets; `.gitignore` already excludes common env files.
- Frontend can use `.env.local` for values like `VITE_GATEWAY_URL` (preferred) or `VITE_BACKEND_URL` (legacy fallback).

### Pre-commit secret scanning

This repository includes a pre-commit hook config using `gitleaks`.

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The hook scans staged changes and blocks commits that include potential secrets.


## Core Features

### Backend

- **LangGraph Agent**: Intelligent tool routing with 3 specialized tools
  - `db_search`: Vector similarity search on PostgreSQL documents
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

### Root Makefile Shortcuts

From repository root:

```bash
make help
make dev
make lint
make typecheck
make test-unit
make test-integration
make test-e2e
make test-integration-gateway-fast
make test-integration-gateway-full
make test-all-integration
```

Documentation workflow:

```bash
make docs-install
make docs-serve
make docs-build
```

### Backend Tests (108 passing)

```bash
cd backend
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest --cov              # With coverage
```

### Verified Local Test Commands

These commands are the canonical local verification flow used during development:

```bash
make lint
make typecheck
make test-unit
```

Direct commands remain available when you need to work inside a subproject:

```bash
# backend
cd backend
uv sync
uv run pytest -q

# frontend
cd ../frontend
npm install
npm run test -- --run

# independent test harness (service-light mode)
cd ../tests
uv sync
SKIP_INTEGRATION=true SKIP_E2E=true uv run pytest -q
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

## Documentation Site

The project now includes a Docusaurus site in `website/` that publishes docs from `docs/`.

- Local run: `make docs-serve`
- Build check: `make docs-build`
- Deploy: GitHub Pages workflow at `.github/workflows/docs-gh-pages.yml`

## Render Deployment (Start Here)

Vecinita now includes a Render Blueprint at [render.yaml](render.yaml) for a multi-service deployment:

- `vecinita-frontend` (web)
- `vecinita-agent` (web)
- `vecinita-embedding` (web)
- `vecinita-scraper` (cron)
- `vecinita-postgres` (Render Postgres)

### Required Render Secrets

Set these in the Render Dashboard for `vecinita-agent` and/or `vecinita-scraper`:

- `DATABASE_URL` (Render Postgres internal connection string)
- `VECTOR_SYNC_TARGET=postgres`
- `GROQ_API_KEY` (or `OPENAI_API_KEY` / `DEEPSEEK_API_KEY`)

Architecture split for production:

- Render Postgres is the vector/document data backend for retrieval and ingestion paths.
- Frontends use local admin or API-key session models.
- Use the Render internal Postgres URL whenever services run in the same Render region.

### CI/CD to Render

Deployment is gated by test success on `main` via [render-deploy.yml](.github/workflows/render-deploy.yml).

Configure repository secrets in GitHub Actions:

- `RENDER_DEPLOY_HOOK_AGENT`
- `RENDER_DEPLOY_HOOK_EMBEDDING`
- `RENDER_DEPLOY_HOOK_FRONTEND`
- `RENDER_DEPLOY_HOOK_SCRAPER`

The deploy workflow triggers only after the `Tests` workflow completes successfully on `main`.

## Documentation

### Getting Started
- **[QUICKSTART.md](docs/guides/QUICKSTART.md)** - Complete setup guide (Docker + Local development)
- **[backend/README.md](backend/README.md)** - Backend API and tools documentation
- **[frontend/README.md](frontend/README.md)** - Frontend components and testing

### Deployment
- Service repositories own their deploy documentation and workflow details.

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

# Run full pipeline (canonical script, local mode)
bash scripts/run_scraper.sh --local --verbose

# Run full pipeline in Docker mode
bash scripts/run_scraper.sh --docker --verbose

# Legacy commands still work and delegate to the canonical script:
bash scripts/data_scrape_load.sh
python scripts/data_scrape_load.py
```

Configuration files:

- `data/urls.txt` - URLs to scrape
- `data/config/recursive_sites.txt` - Sites for recursive crawling
- `data/config/playwright_sites.txt` - JS-heavy sites requiring Playwright
- `data/config/skip_sites.txt` - Domains to skip

## Schema Files

- Active schema and maintenance scripts live under `backend/scripts/`.

## Environment Variables

### Required

```bash
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<db>
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
- **Database**: PostgreSQL + pgvector
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
