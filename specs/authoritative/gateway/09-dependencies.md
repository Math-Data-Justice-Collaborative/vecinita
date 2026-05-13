# Dependencies: Gateway
> Auto-generated: 2026-05-12

Source: `apis/gateway/pyproject.toml`

## Runtime Dependencies (Critical)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | latest | Web framework |
| uvicorn | latest | ASGI server |
| httpx | 0.28.1 (pinned) | Async HTTP client for agent/embedding proxy |
| psycopg2-binary | latest | PostgreSQL driver (documents, job persistence) |
| pydantic | v2 | Request/response validation |
| modal | ≥1.3.5 | Modal SDK for serverless function invocation |
| python-dotenv | ≥1.2.2 (override) | Environment config loading |
| pyyaml | ≥6.0.1 | YAML config defaults |
| python-multipart | ≥0.0.27 | Form data parsing |
| numpy | (transitive) | Cosine similarity computation in embed router |

## Runtime Dependencies (LangChain Stack)

These are declared in `pyproject.toml` but primarily used by the agent service sharing the same dependency file.

| Package | Version | Purpose |
|---------|---------|---------|
| langchain | latest | LLM framework |
| langchain-community | latest | Community integrations |
| langchain-core | ≥1.3.3 | Core abstractions |
| langchain-ollama | ≥1.0.0 | Ollama provider |
| langgraph | ≥1.1.2 | Graph-based agent orchestration |
| litellm | ≥1.83.11 | Multi-provider LLM gateway |
| guardrails-ai | ≥0.5.0 | Input/output validation |

## Optional Dependencies

| Extra | Packages | Purpose |
|-------|----------|---------|
| `embedding` | sentence-transformers, scikit-learn, numpy | Local embedding fallback |
| `scraper` | unstructured, playwright, sentence-transformers, fastembed | Scraper runtime |
| `ci` | pytest, schemathesis, pact-python, tracecov, ruff, black, mypy | CI pipeline |
| `dev` | All CI + jupyter, ipython, unstructured, playwright, docker | Development |

## Internal Dependencies (Monorepo)

| Module | Path | Purpose |
|--------|------|---------|
| `src.config` | `apis/gateway/src/config.py` | Central configuration |
| `src.service_endpoints` | `apis/gateway/src/service_endpoints.py` | Normalized service URLs |
| `src.services.modal.invoker` | `apis/gateway/src/services/modal/invoker.py` | Modal function invocation |
| `src.services.ingestion.*` | `apis/gateway/src/services/ingestion/` | Pipeline persistence |
| `src.services.corpus.*` | `apis/gateway/src/services/corpus/` | Corpus projection |
| `src.utils.*` | `apis/gateway/src/utils/` | Database URL, tags, sanitization |

## Infrastructure Dependencies

| Resource | Type | Required | Purpose |
|----------|------|----------|---------|
| PostgreSQL (Render) | Database | Yes (soft) | Documents read, job persistence |
| Agent service | HTTP service | Yes (soft) | Q&A proxy |
| Modal platform | Serverless | Optional | Embedding/scraper/reindex invocation |
| Render platform | PaaS | Yes | Deployment target |

**Hard vs. soft:** Gateway starts without any dependency. Agent and database failures result in `degraded` health status, not startup failure. Modal is fully optional (controlled by `MODAL_FUNCTION_INVOCATION`).

## Service Dependencies (Runtime)

| Service | Required | Fallback | Impact of Absence |
|---------|----------|----------|-------------------|
| Agent service | Soft | Demo mode, fallback config | Q&A endpoints return demo/error responses |
| Embedding service | Soft | HTTP fallback if Modal off | Embedding endpoints return 503 |
| PostgreSQL | Soft | — | Documents endpoints return 503, job persistence disabled |
| Modal platform | Optional | HTTP proxy to services | Scrape/embed/reindex via HTTP instead of SDK |
