# Backend Quick Reference - New Architecture

## Directory Map

```
backend/
├── src/
│   ├── api/                           # 🌐 API Gateway (main entry point)
│   │   ├── main.py                   # FastAPI application
│   │   ├── models.py                 # API schemas (request/response)
│   │   ├── routers/                  # Endpoint implementations
│   │   │   ├── ask.py               # Q&A endpoints
│   │   │   ├── scrape.py            # Scraping endpoints
│   │   │   ├── embed.py             # Embedding endpoints
│   │   │   └── admin.py             # Admin endpoints
│   │   ├── middleware.py             # Auth & rate limiting
│   │   ├── job_manager.py            # Async job management
│   │   └── static/                   # UI assets
│   │
│   ├── services/                      # 📦 Microservices (pure Python + FastAPI wrapper)
│   │   ├── agent/
│   │   │   ├── server.py            # FastAPI server
│   │   │   ├── models.py            # Agent-specific models
│   │   │   ├── tools/               # LangGraph tools
│   │   │   ├── data/                # Agent config
│   │   │   └── utils/               # Agent utilities
│   │   │
│   │   ├── embedding/
│   │   │   ├── server.py            # FastAPI server
│   │   │   ├── models.py            # Embedding models
│   │   │   ├── client.py            # HTTP client
│   │   │   └── modal_app.py         # Modal deployment
│   │   │
│   │   └── scraper/
│   │       ├── server.py            # FastAPI server
│   │       ├── models.py            # Scraper models
│   │       ├── cli.py               # CLI interface
│   │       ├── scraper.py           # Core logic
│   │       ├── loaders.py           # Document loaders
│   │       ├── processors.py        # Text processing
│   │       ├── uploader.py          # DB uploader
│   │       └── utils.py             # Utilities
│   │
│   └── utils/                         # 🔧 Shared Utilities
│       ├── supabase_embeddings.py    # Supabase client
│       └── ...
│
├── data/                              # 📄 Data Files (workspace root)
│   ├── urls.txt                      # URLs to scrape
│   ├── config/                       # Scraper configuration
│   │   ├── recursive_sites.txt
│   │   ├── playwright_sites.txt
│   │   └── skip_sites.txt
│   ├── input/                        # Input files
│   └── output/                       # Generated chunks (at runtime)
│
├── tests/                             # ✅ Tests (mirrors src structure)
│   ├── test_api/                     # API gateway tests
│   ├── test_services/
│   │   ├── agent/                    # Agent tests
│   │   ├── embedding/                # Embedding tests
│   │   └── scraper/                  # Scraper tests
│   ├── test_utils/                   # Utils tests
│   ├── integration/                  # Cross-service tests
│   └── e2e/                          # End-to-end tests
│
├── scripts/                           # 🚀 Deployment/utility scripts
│   ├── cron_scraper.sh               # Cron job wrapper
│   ├── clean_and_load.py             # DB cleanup
│   └── ...
│
├── pyproject.toml                     # 📦 Dependencies & entry points
├── Dockerfile                         # 🐳 API container
├── Dockerfile.embedding               # 🐳 Embedding service container
├── Dockerfile.scraper                 # 🐳 Scraper container
│
├── REFACTORING_COMPLETE.md            # ✅ What changed
├── ARCHITECTURE_DECISIONS.md          # 🎯 Why & how
└── QUICK_REFERENCE.md                 # 📖 This file
```

## Running Locally

### Option 1: All Services (Recommended for Development)

```bash
# Terminal 1 - API Gateway (main entry point)
cd backend
uv sync
uv run -m uvicorn src.api.main:app --reload --port 8002

# Terminal 2 - Agent Service
uv run -m uvicorn src.services.agent.server:app --reload --port 8000

# Terminal 3 - Embedding Service
uv run -m uvicorn src.services.embedding.server:app --reload --port 8001
```

Access API at: http://localhost:8002
- Docs: http://localhost:8002/docs
- Q&A: http://localhost:8002/ask?question=hello
- Admin: http://localhost:8002/admin/health

### Option 2: Docker Compose (Full Stack)

```bash
cd ..  # Go to workspace root
docker-compose up
```

### Option 3: Single Service (Testing)

```bash
# Test just Agent Service
cd backend
uv run -m uvicorn src.services.agent.server:app --port 8000

# Test with curl
curl http://localhost:8000/ask?question=test
```

## Testing

### Run All Tests
```bash
cd backend
uv run pytest
```

### Run Specific Tests
```bash
# API tests only
uv run pytest tests/test_api/

# Agent service tests
uv run pytest tests/test_services/agent/

# With coverage
uv run pytest --cov
```

## Common Tasks

### Add New Endpoint to API

1. **Create router** if needed:
   ```python
   # src/api/router_myfeature.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/myfeature", tags=["My Feature"])
   
   @router.get("")
   async def my_endpoint():
       return {"status": "ok"}
   ```

2. **Register in API**:
   ```python
   # src/api/main.py
   from .router_myfeature import router as myfeature_router
   app.include_router(myfeature_router, prefix="/api")
   ```

### Add New Service Model

```python
# src/services/myservice/models.py
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    """Description of my model."""
    field1: str = Field(..., description="Field 1")
    field2: int = Field(default=0, description="Field 2")
```

### Test a Service in Isolation

```python
# tests/test_services/myservice/test_myservice.py
import pytest
from src.services.myservice.server import app

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)

def test_my_endpoint(client):
    response = client.get("/my-endpoint")
    assert response.status_code == 200
```

### Use Service Models in Code

```python
from src.services.agent.models import ModelSelection

selection: ModelSelection = {
    "provider": "groq",
    "model": "llama-3.1-70b",
    "locked": False
}
```

## Import Patterns

### ✅ Correct Imports

```python
# From API
from src.api.models import AskRequest, AskResponse
from src.api.main import app

# From service
from src.services.agent.models import ModelSelection
from src.services.agent.server import app as agent_app

# From utils
from src.utils.supabase_embeddings import SupabaseEmbeddings

# In tests
from src.services.agent.models import ModelSelection
```

### ❌ Avoid These

```python
# Don't use relative imports that are ambiguous
from .models import Something        # Avoid

# Don't import from wrong level
from src.agent.models import X       # WRONG - agent moved
from src.gateway.main import app     # WRONG - gateway renamed

# Don't cross-import between services
from src.services.agent import X     # ❌ For embedding service
```

## Port Reference

| Service | Port | Purpose | URL |
|---------|------|---------|-----|
| **API Gateway** | 8002 | Main entry point | http://localhost:8002 |
| **Agent** | 8000 | LangGraph Q&A | http://localhost:8000 |
| **Embedding** | 8001 | Text embeddings | http://localhost:8001 |
| **Scraper** | N/A | Batch/CLI only | `python -m src.services.scraper.cli` |

## Environment Variables

Essential `.env` file:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# LLM Providers (at least one required)
GROQ_API_KEY=your-key
DEEPSEEK_API_KEY=your-key

# Service URLs (if running separately)
AGENT_SERVICE_URL=http://localhost:8000
EMBEDDING_SERVICE_URL=http://localhost:8001

# Optional
DEFAULT_PROVIDER=groq
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Troubleshooting

### "No module named 'src.api'"
```bash
# Make sure you're in backend directory
cd backend
# Run pytest from backend root
uv run pytest
```

### "Connection refused on port 8000"
Agent service not running. Start it in another terminal:
```bash
uv run -m uvicorn src.services.agent.server:app --reload --port 8000
```

### "Import from src.gateway failed"
Old code using renamed module. Update imports:
```python
# OLD
from src.gateway.main import app

# NEW
from src.api.main import app
```

### Tests are slow
Run only what you need:
```bash
# Just unit tests
uv run pytest tests/test_api/ -v

# Skip integration/e2e
uv run pytest -m "not integration and not e2e"
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/api/main.py` | Main FastAPI application - START HERE for routing |
| `src/api/models.py` | API request/response schemas - CHECK HERE for endpoints |
| `src/services/agent/server.py` | Agent Q&A service - MODIFY for agent behavior |
| `src/services/embedding/server.py` | Embedding service - MODIFY for embedding behavior |
| `src/services/scraper/cli.py` | Scraper CLI - MODIFY for scraping logic |
| `pyproject.toml` | Dependencies and entry points |
| `tests/conftest.py` | Pytest fixtures and configuration |

## CLI Commands

```bash
# From backend directory

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run pyright src/

# Run scraper
uv run python -m src.services.scraper.cli --help

# Run API
uv run -m uvicorn src.api.main:app --reload
```

---

## Quick Navigation

- **Need to fix an API issue?** → `src/api/`
- **Need to fix Agent?** → `src/services/agent/`
- **Need to fix Embedding?** → `src/services/embedding/`
- **Need to fix Scraper?** → `src/services/scraper/`
- **Need to add shared utility?** → `src/utils/`
- **Need to write tests?** → `tests/test_*/` (mirror of src/)
- **Need to change how API works?** → `src/api/main.py`
- **Need to understand architecture?** → `ARCHITECTURE_DECISIONS.md`

---

**Last Updated:** February 8, 2026  
**Architecture Version:** 1.0  
**For questions:** See ARCHITECTURE_DECISIONS.md
