# Vecinita Dependencies

> Auto-generated dependency inventory. Last updated: 2026-05-11.

## Overview

| Ecosystem | Manifests scanned | Total packages |
|-----------|-------------------|----------------|
| Python | 12 | ~85 unique |
| Node | 4 | ~95 unique |
| Infrastructure | 5 services | 1 database |

## Python Dependencies

### Runtime

| Package | Version constraint | Used by |
|---------|--------------------|---------|
| aiohttp | ==3.13.5 (override) | Gateway, Scraper |
| beautifulsoup4 | (any) | Gateway |
| charset-normalizer | >=3.3.0 | Scraper |
| crawl4ai | >=0.4.0 | Scraper |
| cryptography | >=46.0.7 | Gateway |
| ddgs | >=9.10.0 | Gateway |
| docling | >=0.4.0 | Scraper |
| fastembed | >=0.7.4 | Embedding (Modal) |
| fastapi | >=0.100 – >=0.135.1 | Gateway, Scraper, Embedding, Model, DM API, Tests |
| filelock | >=3.20.3 | Gateway |
| gotrue | >=2.0.0 | Gateway |
| guardrails-ai | >=0.5.0 | Gateway |
| httpx | ==0.28.1 (override) | Gateway, Scraper, Model, DM API, Service-clients, Tests |
| langchain | >=0.1.0 | Gateway, Scraper |
| langchain-community | (any) | Gateway |
| langchain-core | >=1.3.3 | Gateway |
| langchain-huggingface | (any) | Gateway |
| langchain-ollama | >=1.0.0 | Gateway |
| langchain-tavily | (any) | Gateway |
| langchain-text-splitters | >=1.1.2 | Gateway |
| langdetect | (any) | Gateway |
| langgraph | >=1.1.2 | Gateway |
| langgraph-checkpoint | >=4.0.0 | Gateway |
| langsmith | >=0.6.3 | Gateway |
| litellm | >=1.83.11 | Gateway |
| marshmallow | >=3.26.2 | Gateway |
| modal | >=0.59.0 – >=1.3.5 | Gateway, Scraper, Embedding, Model, DM API, Service-clients |
| ollama | >=0.4.0 | Model (Modal) |
| onnxruntime | >=1.18.0,<1.24.0.dev (win32) | Gateway |
| orjson | >=3.11.6 | Gateway |
| pillow | >=12.1.1 (py<3.13) | Gateway |
| protobuf | >=6.33.5 | Gateway |
| psycopg2-binary | >=2.9.9 | Gateway, Scraper |
| pydantic | >=2.0 – >=2.6 | Gateway, Scraper, Model, DM API, Shared-config, Service-clients, Shared-schemas, Tests |
| pydantic-settings | >=2.0 – >=2.2 | Model, DM API, Shared-config |
| pygments | >=2.20.0 | Gateway |
| pyjwt | >=2.12.0 | Gateway |
| pypdf | >=5.0.0 – >=6.10.1 | Gateway, Scraper |
| python-dotenv | >=1.2.2 (override) | Scraper, Tests |
| python-json-logger | >=2.0.0 | Shared-logging |
| python-multipart | >=0.0.27 | Gateway |
| pyyaml | >=6.0.0 – >=6.0.1 | Gateway, Shared-config |
| requests | >=2.31.0 – >=2.33.0 | Gateway, Tests |
| structlog | >=23.0 | Scraper |
| tiktoken | >=0.5.0 | Scraper |
| tokenizers | >=0.22.0,<0.23.0 | Gateway |
| tqdm | (any) | Gateway |
| transformers | >=5.0.0rc3 | Gateway |
| urllib3 | >=2.7.0 | Gateway |
| uvicorn | >=0.23.0 – (any) | Gateway, Scraper, DM API |

### Dev / CI only

| Package | Version constraint | Used by |
|---------|--------------------|---------|
| black | ==26.3.1 | Gateway (dev/ci), Scraper, Tests |
| hypothesis | >=6.0.0 | Gateway (dev/ci), Scraper |
| ipython | >=8.20.0 | Gateway (dev) |
| isort | >=5.12.0 | Scraper (dev) |
| jupyter | >=1.0.0 | Gateway (dev) |
| mypy | >=1.5.0 – >=1.8.0 | Gateway (dev/ci), Scraper, Model |
| pact-python | >=3.3.0 | Gateway (ci), Scraper (dev) |
| playwright | >=1.40.0 | Gateway (dev), Tests |
| pre-commit | >=3.0 | Scraper (dev) |
| pytest | >=7.4 – >=9.0.3 | Gateway (dev/ci), Scraper, Embedding, Model, Tests |
| pytest-asyncio | >=0.21 – >=0.24.0 | Gateway (dev/ci), Scraper, Model, Tests |
| pytest-cov | >=4.1 – >=7.0.0 | Gateway (dev/ci), Scraper, Embedding, Model, Tests |
| pytest-mock | >=3.11 | Scraper (dev) |
| respx | >=0.21.0 | Service-clients (dev) |
| ruff | >=0.1.0 – >=0.11.0 | Gateway (dev/ci), Scraper, Embedding, Model, Shared-config, Service-clients, Shared-schemas, Shared-logging, Tests |
| schemathesis | >=4.14.3 | Gateway (dev/ci), Scraper |
| tracecov | >=0.19.3,<0.20 | Gateway (dev/ci) |
| types-PyYAML | >=6.0.12 | Gateway (dev/ci) |
| types-requests | >=2.32.4.20260324 | Gateway (dev/ci) |

### Optional extras

| Extra group | Packages | Used by |
|-------------|----------|---------|
| agent | (empty — base deps suffice) | Agent service |
| embedding | sentence-transformers, scikit-learn, numpy | Embedding service (Render) |
| scraper | unstructured[doc,docx,ppt,pdf], playwright, sentence-transformers, fastembed | Scraper workers |
| docker | docker>=7.0.0 | Local orchestration |
| ml | tf-keras>=2.20.1, torch>=2.9.1 | Local experimentation |
| ci | pytest, pytest-asyncio, pytest-cov, hypothesis, schemathesis, tracecov, pact-python, types-*, black, ruff, mypy | CI pipeline |
| visualization | graphviz, pygraphviz | Graph rendering |
| all | dev + scraping + docker + visualization + embedding | Full local dev |

## Node Dependencies

### Runtime

| Package | Version | Used by |
|---------|---------|---------|
| @docusaurus/core | ^3.8.1 | Website |
| @docusaurus/preset-classic | ^3.8.1 | Website |
| @emotion/react | 11.14.0 | Chat FE, DM FE |
| @emotion/styled | 11.14.1 | Chat FE, DM FE |
| @mdx-js/react | ^3.1.0 | Website |
| @mui/icons-material | 7.3.5 | Chat FE, DM FE |
| @mui/material | 7.3.5 | Chat FE, DM FE |
| @popperjs/core | 2.11.8 | Chat FE, DM FE |
| @radix-ui/react-* | 1.1.x–2.2.x | Chat FE, DM FE |
| class-variance-authority | ^0.7.1 | Chat FE, DM FE |
| clsx | ^2.1.1 | Chat FE, DM FE, Website |
| cmdk | 1.1.1 | Chat FE, DM FE |
| date-fns | 3.6.0 | Chat FE, DM FE |
| embla-carousel-react | 8.6.0 | Chat FE, DM FE |
| input-otp | 1.4.2 | Chat FE, DM FE |
| lucide-react | ^0.487.0 | Chat FE, DM FE |
| motion | 12.23.24 | Chat FE, DM FE |
| msw | ^2.12.7 | Chat FE |
| next-themes | 0.4.6 | Chat FE, DM FE |
| prism-react-renderer | ^2.4.1 | Website |
| react | 18.3.1 (peer) / ^19.0.0 | Chat FE, DM FE / Website |
| react-day-picker | 8.10.1 | Chat FE, DM FE |
| react-dnd | 16.0.1 | Chat FE, DM FE |
| react-dnd-html5-backend | 16.0.1 | Chat FE, DM FE |
| react-dom | 18.3.1 (peer) / ^19.0.0 | Chat FE, DM FE / Website |
| react-hook-form | 7.55.0 | Chat FE, DM FE |
| react-markdown | ^10.1.0 | Chat FE |
| react-popper | 2.3.0 | Chat FE, DM FE |
| react-resizable-panels | 2.1.7 | Chat FE, DM FE |
| react-responsive-masonry | 2.7.1 | Chat FE, DM FE |
| react-router-dom | ^6.30.3 | Chat FE |
| react-router | 7.13.0 | DM FE |
| react-slick | 0.31.0 | Chat FE, DM FE |
| recharts | 2.15.2 | Chat FE, DM FE |
| remark-gfm | ^4.0.1 | Chat FE |
| sonner | 2.0.3 | Chat FE, DM FE |
| tailwind-merge | ^3.2.0 | Chat FE, DM FE |
| uuid | ^13.0.0 | Chat FE |
| vaul | 1.1.2 | Chat FE, DM FE |

### Dev only

| Package | Version | Used by |
|---------|---------|---------|
| @docusaurus/module-type-aliases | ^3.9.2 | Website |
| @docusaurus/tsconfig | ^3.9.2 | Website |
| @docusaurus/types | ^3.9.2 | Website |
| @eslint/js | ^9.39.0 | DM FE |
| @pact-foundation/pact | ^16.3.0 | Chat FE, DM FE |
| @playwright/test | ^1.55.0 | Chat FE, DM FE |
| @tailwindcss/vite | 4.1.12 | Chat FE, DM FE |
| @testing-library/jest-dom | ^6.9.1 / 6.8.0 | Chat FE, DM FE |
| @testing-library/react | ^16.3.2 / 16.3.0 | Chat FE, DM FE |
| @testing-library/user-event | ^14.6.1 / 14.6.1 | Chat FE, DM FE |
| @types/node | ^25.0.10 / ^25.5.0 | Chat FE, Website |
| @types/react | ^19.2.14 | Website |
| @types/react-dom | ^18.3.7 / ^19.2.3 | Chat FE, Website |
| @typescript-eslint/* | ^8.31.1 | Chat FE |
| @vitejs/plugin-react | 4.7.0 | Chat FE, DM FE |
| @vitest/coverage-v8 | ^4.0.18 / ^4.1.0 | Chat FE, DM FE |
| @vitest/ui | ^4.0.18 | Chat FE |
| eslint | ^8.57.1 / ^9.39.0 | Chat FE, DM FE |
| eslint-plugin-react | ^7.37.5 | Chat FE |
| eslint-plugin-react-hooks | ^5.2.0 | Chat FE, DM FE |
| eslint-plugin-react-refresh | ^0.4.21 | DM FE |
| globals | ^15.15.0 | DM FE |
| jsdom | 25.0.1 / 26.1.0 | Chat FE, DM FE |
| openapi-typescript | ^7.13.0 | DM FE |
| prettier | ^3.5.3 | Chat FE |
| shadcn | ^3.8.5 | Chat FE |
| tailwindcss | 4.1.12 | Chat FE, DM FE |
| tw-animate-css | ^1.4.0 / 1.3.8 | Chat FE, DM FE |
| typescript | ^5.8.3 / ^5.9.3 | Chat FE, DM FE, Website |
| typescript-eslint | ^8.47.0 | DM FE |
| vite | ^6.4.1 | Chat FE, DM FE |
| vitest | ^4.0.18 / ^4.1.0 | Chat FE, DM FE |

## Infrastructure

### Render services

| Service | Runtime | Dockerfile | Plan |
|---------|---------|------------|------|
| vecinita-agent | docker | `apis/agent/Dockerfile` | starter |
| vecinita-frontend | docker | `frontends/chat/Dockerfile` | starter |
| vecinita-gateway | docker | `apis/gateway/Dockerfile.gateway` | starter |
| vecinita-data-management-frontend-v1 | docker | `frontends/data-management/Dockerfile` | starter |
| vecinita-data-management-api-v1 | docker | `modal-apps/scraper/Dockerfile` | starter |

### Databases

| Name | Engine | Version | Plan |
|------|--------|---------|------|
| vecinita-postgres | PostgreSQL | 16 | basic-256mb |

### Modal apps

| App | Repository | Python version |
|-----|------------|----------------|
| vecinita-scraper | modal-apps/scraper | >=3.11 |
| vecinita-embedding | modal-apps/embedding-modal | >=3.11 |
| vecinita-model | modal-apps/model-modal | >=3.11 |

### Git submodules

| Path | Remote URL | Branch |
|------|------------|--------|
| frontends/chat | https://github.com/Math-Data-Justice-Collaborative/Vecinitafrontend.git | dev |
| frontends/data-management | https://github.com/Math-Data-Justice-Collaborative/vecinita-data-management-frontend.git | main |
| apis/data-management-api | https://github.com/Math-Data-Justice-Collaborative/vecinita-data-management.git | main |
| modal-apps/scraper | https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper.git | main |
| modal-apps/embedding-modal | https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding.git | main |
| modal-apps/model-modal | https://github.com/Math-Data-Justice-Collaborative/vecinita-model.git | main |

## External Services & APIs

| Service | Purpose | Auth mechanism |
|---------|---------|----------------|
| DeepSeek | LLM provider (chat) | API key (`DEEPSEEK_API_KEY`) |
| Groq | LLM provider (fast inference) | API key (`GROQ_API_KEY`) |
| Hugging Face | Model hub access | Token (`HUGGINGFACE_ACCESS_TOKEN`) |
| LangSmith | Tracing & observability | API key (`LANGSMITH_API_KEY`) |
| Modal | Serverless compute (scraper, embedding, model) | Token pair (`MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`) |
| Ollama (hosted) | Local LLM inference relay | Base URL (`OLLAMA_BASE_URL`) |
| OpenAI | LLM provider | API key (`OPENAI_API_KEY`) |
| PostgreSQL (Render) | Persistent data + pgvector | Connection string (`DATABASE_URL`) |
| Render | PaaS hosting | Deploy hooks / API key |
| Supabase | Auth, edge functions | URL + anon key (`SUPABASE_URL` / `SUPABASE_KEY`) |
| Tavily | Web search API | API key (`TAVILY_API_KEY`) |

## Version constraints & overrides

| Package | Override | Reason |
|---------|----------|--------|
| aiohttp | ==3.13.5 | Align with litellm; avoids ResolutionImpossible |
| httpx | ==0.28.1 | Pinned to match litellm transitive requirement |
| lxml | >=6.1.0 | CVE-2026-41066 constraint |
| python-dotenv | >=1.2.2 | litellm declares ==1.0.1; override needed for newer features |
| vite | 6.3.5 (pnpm) | Chat FE and DM FE pin via pnpm overrides |
| werkzeug | >=3.1.6 | Forced patched version (transitive via schemathesis/tensorboard) |

## Cross-service shared dependencies

| Package | Versions across services | Aligned? |
|---------|--------------------------|----------|
| fastapi | (any), >=0.100, >=0.110, >=0.115.0, >=0.116.0, >=0.135.1 | Drift (floor varies) |
| httpx | ==0.28.1 (root override), >=0.25.0, >=0.27.0, >=0.28.1 | Aligned via override |
| modal | >=0.59.0, >=0.73.0, >=1.3.5 | Drift (scraper/model lag) |
| pydantic | (any), >=2.0, >=2.6 | Mostly aligned (2.x) |
| psycopg2-binary | (any), >=2.9.9 | Aligned |
| pytest | >=7.4, >=8.0.0, >=8.3.5, >=9.0.0, >=9.0.3 | Drift (test suites) |
| ruff | >=0.1.0, >=0.2.0, >=0.3.0, >=0.8.0, >=0.11.0 | Drift (floors vary) |
| tailwindcss | 4.1.12 | Aligned (Chat FE & DM FE) |
| typescript | ^5.8.3, ^5.9.3 | Minor drift |
| vite | ^6.4.1 (dep) / 6.3.5 (override) | Aligned via pnpm override |
| vitest | ^4.0.18, ^4.1.0 | Minor drift |
