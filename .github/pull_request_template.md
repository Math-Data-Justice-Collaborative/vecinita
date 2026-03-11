## Vecinita Pull Request Template

### 1. Description of changes

- What does this PR do?
- Which part(s) of the system are affected? (FastAPI app, scraper, vector loader, prompts, UI, tests, infra, etc.)

_Summary:_
<!-- Provide a concise, high-level description of the change. -->

_Details:_
<!-- List key implementation details, new modules, important refactors, or behavior changes. -->

### 2. Testing performed

**Pytest commands run (copy/paste exact commands):**
<!-- e.g., `uv run pytest -m "unit"` or `uv run pytest tests/test_main.py` -->
- 

**pytest markers covered in this PR:**
- [ ] `unit`
- [ ] `integration`
- [ ] `db`
- [ ] `api`
- [ ] `ui`
- [ ] Other: <!-- describe if applicable -->

**Test notes / output (if relevant):**
<!-- Mention any flaky tests, temporarily skipped tests, or special setup required. -->

### 3. Impact on data pipeline & Q&A behavior

**Data scraping / ingestion:**
- [ ] No changes
- [ ] Changes to scraper behavior (URLs, loaders, rate limiting, Playwright usage, etc.)
- [ ] Changes to config files (`data/config/*.txt`, `data/urls.txt`)

**Vector storage / embeddings / Supabase:**
- [ ] No changes
- [ ] Changes to chunking or embedding generation
- [ ] Changes to Supabase schema or RPCs (e.g., `search_similar_documents`)
- [ ] Potential impact on `unique_content_source` deduplication

**Q&A engine / prompts / language handling:**
- [ ] No changes
- [ ] Changes to `/ask` endpoint logic or routing
- [ ] Changes to prompt templates (English/Spanish)
- [ ] Changes to source attribution or answer formatting

_If any box above is checked, briefly describe the expected impact and any migration or backfill steps needed:_

### 4. Docker & environment variables

**Docker / Compose:**
- [ ] No Docker changes
- [ ] Updated `docker-compose` configuration
- [ ] Updated Dockerfile(s)

**Environment variables:**
- [ ] No env var changes
- [ ] New env vars required
- [ ] Existing env vars changed or removed

_List any new or changed env vars (name + brief purpose):_
<!-- e.g., `GROQ_API_KEY` – API key for Llama 3.1 via Groq -->

_Deployment / runtime notes (if any):_
<!-- e.g., "Requires `.env` update in production and staging before deploy." -->

### 5. Dependencies & UV sync checklist

**Python dependencies (pyproject / uv):**
- [ ] No dependency changes
- [ ] `pyproject.toml` updated
- [ ] `uv.lock` or lockfile updated (if applicable)
- [ ] `uv sync` run locally after changes

_If dependencies changed, explain why and call out any version pinning or platform-specific notes:_

### 6. Breaking changes / migrations

- [ ] No breaking changes
- [ ] Breaking change (describe below)

_Describe any breaking changes, required DB migrations, or one-time scripts:_

### 7. Related issues / context

- Related issue(s): <!-- e.g., Closes #123, Relates to #456 -->
- Additional context or design notes (if any):

### 8. Checklist

- [ ] Code follows project style and guidelines
- [ ] Tests added/updated as needed
- [ ] `uv run pytest` passes locally for relevant markers
- [ ] Docs / comments updated where appropriate
- [ ] Manual testing performed against running FastAPI app (if applicable)

<!--
Notes:
- Prefer `uv` for running tests and dev commands (e.g., `uv run pytest`).
- Use pytest markers (`unit`, `integration`, `db`, `api`, `ui`) to classify tests.
- When touching the data pipeline (scraper, vector loader, Supabase), be explicit about
  potential impacts on existing data and search behavior.
-->
