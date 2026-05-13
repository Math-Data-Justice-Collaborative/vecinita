# User Journeys Diagram: Embedding Worker
> Auto-generated: 2026-05-12

## J1: Gateway Single Embedding Journey

```mermaid
journey
    title Gateway Embeds a User Question
    section Request
      User submits question: 5: End User
      Gateway receives /api/v1/ask: 5: Gateway
      Gateway resolves embed_query: 4: Gateway
    section Embedding
      fn.remote(question_text): 4: Gateway, Modal
      Load model from Volume: 3: Embedding Worker
      Embed text (384-dim): 5: Embedding Worker
      Return vector dict: 5: Embedding Worker
    section Response
      Query PostgreSQL neighbors: 4: Gateway
      Return answer to user: 5: Gateway
```

## J2: Gateway Batch Embedding Journey

```mermaid
journey
    title Gateway Embeds Document Batch
    section Request
      Scraper produces text chunks: 5: Scraper
      Gateway resolves embed_batch: 4: Gateway
    section Embedding
      fn.remote(text_list): 4: Gateway, Modal
      Load model from Volume: 3: Embedding Worker
      Embed all texts: 5: Embedding Worker
      Return vectors dict: 5: Embedding Worker
    section Persistence
      Write vectors to PostgreSQL: 4: Gateway
      Vectors available for RAG: 5: Gateway
```

## J3: Developer Local Testing Journey

```mermaid
journey
    title Developer Tests Locally
    section Setup
      Clone repository: 5: Developer
      Install dependencies: 4: Developer
    section Test
      Run make test: 5: Developer
      All tests pass (95%+ coverage): 5: CI
    section Lint
      Run make lint: 5: Developer
      ruff checks pass: 5: CI
    section Local API
      Start uvicorn server: 4: Developer
      POST /embed with test query: 5: Developer
      Verify 384-dim response: 5: Developer
```

## J4: CI/CD Deploy Journey

```mermaid
journey
    title CI/CD Deploys to Modal
    section Quality
      Push to main: 5: Developer
      CI runs lint: 5: GitHub Actions
    section Test
      CI runs pytest: 5: GitHub Actions
      Coverage >= 95%: 5: GitHub Actions
    section Deploy
      Verify Modal credentials: 4: GitHub Actions
      modal deploy main.py: 4: GitHub Actions
      Functions live on Modal: 5: Modal
```

## J5: Cold Start Recovery

```mermaid
journey
    title Cold Start After Idle Period
    section Trigger
      Gateway calls embed_query: 4: Gateway
      Modal spins up container: 3: Modal
    section Initialization
      Mount Volume at /models: 4: Modal
      Import fastembed: 3: Embedding Worker
      Load model from cache: 3: Embedding Worker
      Run warmup query: 4: Embedding Worker
    section Ready
      Process actual query: 5: Embedding Worker
      Return vector in <2s: 5: Embedding Worker
      Subsequent calls are warm: 5: Embedding Worker
```

See: [User Journeys](../05-user-journeys.md)
