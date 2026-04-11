# Backend Development Guide

## Setup

```bash
cd backend
uv sync
uv run uvicorn src.agent.main:app --reload
```

## Testing

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Watch mode
uv run pytest-watch

# Specific markers
uv run pytest -m integration
uv run pytest -m "not integration"
```

## Code Standards

### Black (Formatter)
```bash
uv run black src tests scripts
```

### Ruff (Linter)
```bash
uv run ruff check --fix src tests
```

### Pyright (Type Checker)
```bash
uv run pyright src
```

## Project Structure

```
backend/
├── src/
│   ├── agent/              # FastAPI + LangGraph Q&A agent
│   │   ├── main.py         # FastAPI application
│   │   ├── tools/          # Agent tools
│   │   │   ├── db_search.py
│   │   │   ├── static_response.py
│   │   │   └── web_search.py
│   │   ├── graph/          # LangGraph workflow
│   │   └── prompts/        # LLM prompts
│   ├── scraper/            # Web scraping service
│   │   ├── scraper.py      # Core scraper
│   │   ├── loaders.py      # Document loaders
│   │   ├── processors.py   # Text processing
│   │   └── uploader.py     # DB uploader
│   ├── embedding_service/  # Embedding generation
│   ├── cli/                # CLI utilities
│   └── utils/              # Helper functions
├── tests/                  # Unit & integration tests
├── scripts/                # Automation scripts
├── Dockerfile             # Production image
├── pyproject.toml         # Dependencies & config
└── README.md
```

## Key Files

- **src/agent/main.py** - Main FastAPI app with `/ask` endpoint
- **src/agent/graph/** - LangGraph workflow definitions
- **tests/test_*.py** - Unit tests
- **scripts/data_scrape_load.sh** - Data pipeline orchestrator

## Common Tasks

### Add a new tool
1. Create `src/agent/tools/my_tool.py`
2. Implement with `@tool` decorator
3. Add to agent graph in `src/agent/graph/`
4. Write tests in `tests/test_my_tool.py`

### Update dependencies
```bash
uv add package_name
```

### Run linting
```bash
uv run black src tests scripts
uv run ruff check --fix src tests
```

## Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Deployment

See [docs/RENDER_DEPLOYMENT_THREE_SERVICES.md](../docs/RENDER_DEPLOYMENT_THREE_SERVICES.md)

## Documentation

- [API Documentation](../docs/API_INTEGRATION_SPEC.md)
- [Architecture](../docs/ARCHITECTURE_MICROSERVICE.md)
- [Database Guide](../docs/DB_SEARCH_DIAGNOSTIC_GUIDE.md)
