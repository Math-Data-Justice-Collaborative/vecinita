# User Journeys: Embedding Worker
> Auto-generated: 2026-05-12

## J1: Gateway Embeds a User Question (Single)

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | End user | Submits question via chat UI | Gateway receives `/api/v1/ask?question=...` |
| 2 | Gateway | Resolves `embed_query` function | `modal.Function.from_name("vecinita-embedding", "embed_query")` |
| 3 | Gateway | Calls `fn.remote(question_text)` | Modal routes to embedding worker container |
| 4 | Embedding Worker | Loads model (warm: instant, cold: ~5-10s) | fastembed `TextEmbedding` initialized |
| 5 | Embedding Worker | Embeds text → 384-dim vector | `list(model.embed([text]))[0].tolist()` |
| 6 | Embedding Worker | Returns `{"embedding": [...], "model": "...", "dimension": 384}` | Modal serializes and returns |
| 7 | Gateway | Receives vector, queries PostgreSQL for nearest neighbors | RAG retrieval proceeds |
| 8 | Gateway | Returns answer to end user | Chat response with sources |

## J2: Gateway Embeds a Document Batch

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Scraper pipeline | Produces batch of document chunks | Text list ready for embedding |
| 2 | Gateway | Resolves `embed_batch` function | `modal.Function.from_name("vecinita-embedding", "embed_batch")` |
| 3 | Gateway | Calls `fn.remote(text_list)` | Modal routes to embedding worker container |
| 4 | Embedding Worker | Loads model | fastembed `TextEmbedding` initialized |
| 5 | Embedding Worker | Embeds all texts → list of 384-dim vectors | `list(model.embed(queries))` |
| 6 | Embedding Worker | Returns `{"embeddings": [[...], ...], "model": "...", "dimension": 384}` | Modal serializes and returns |
| 7 | Gateway | Writes vectors to `agent.vectors` in PostgreSQL | Vectors persisted for retrieval |

## J3: Developer Tests Locally

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Developer | Clones `modal-apps/embedding-modal` | Repository ready |
| 2 | Developer | Runs `pip install ".[dev]"` | Dependencies installed |
| 3 | Developer | Runs `make test` | pytest executes unit + integration tests with fakes |
| 4 | Developer | Runs `make lint` | ruff format + ruff check |
| 5 | Developer | Starts local FastAPI: `uvicorn vecinita.api:app` | HTTP server on localhost |
| 6 | Developer | Sends `POST /embed {"query": "test"}` | Returns embedding response |
| 7 | Developer | Verifies response shape and dimensions | 384-dim vector confirmed |

## J4: Developer Deploys to Modal

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Developer | Sets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` | Modal CLI authenticated |
| 2 | Developer | Runs `modal deploy src/vecinita/app.py` | Modal builds image, uploads code |
| 3 | Modal | Builds `debian_slim` + `fastembed>=0.7.4` image | Container image cached |
| 4 | Modal | Creates/attaches `embedding-models` Volume | Model cache available at `/models` |
| 5 | Modal | Registers `embed_query` and `embed_batch` functions | Functions available for `.remote()` calls |
| 6 | Developer | Verifies via `modal run` or gateway test | Functions respond correctly |

## J5: CI/CD Pipeline Deploys on Push

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Developer | Pushes to `main` branch | GitHub Actions triggered |
| 2 | CI | Runs lint job (`make lint`) | ruff checks pass |
| 3 | CI | Runs test job (`make test`) | pytest passes with ≥95% coverage |
| 4 | CI | Verifies Modal credentials from secrets | `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` present |
| 5 | CI | Runs `modal deploy main.py` | New version deployed to Modal |
| 6 | CI | Deploy job completes | Updated functions live |

## J6: Cold Start Recovery

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Gateway | Calls `embed_query` after period of inactivity | Modal spins up new container |
| 2 | Modal | Provisions container with cached image | debian_slim + fastembed ready |
| 3 | Modal | Mounts `embedding-models` Volume at `/models` | Cached model files available |
| 4 | Embedding Worker | Calls `load_runtime_model()` | `TextEmbedding` loads from Volume cache |
| 5 | Embedding Worker | Runs warmup: `model.embed(["warmup"])` | Model weights loaded into memory |
| 6 | Embedding Worker | Processes actual query | Response in <2s (warm) |
| 7 | Subsequent calls | Hit warm container | No model reload needed |

See: [User Personas](04-user-personas.md) | [Data Flow](06-data-flow.md) | [Sequence Flows](diagrams/sequence-flows.md)
