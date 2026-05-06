## Vecinita Pull Request Template

### 1. Description of changes

- What does this PR do?
- Which part(s) of the system are affected? (FastAPI app, scraper, vector loader, prompts, UI, tests, infra, etc.)

_Summary:_
<!-- Provide a concise, high-level description of the change. -->

_Details:_
<!-- List key implementation details, new modules, important refactors, or behavior changes. -->

### 2. Verification performed

**Commands run (copy/paste exact commands):**
<!-- Include focused checks + final repo gate -->
- 
- `make ci`

**Result summary:**
<!-- Note pass/fail and any important context -->

### 3. CI attestation gate (required for merge)

- [ ] `.ci/required-checks.json` reviewed (or updated if contract changed)
- [ ] `.ci/ci-attestation.json` regenerated on this branch
- [ ] `git_head` in attestation matches current branch tip
- [ ] `make ci-attestation-validate` passes locally

_Attestation refresh command(s) used:_
<!-- e.g., `make ci-attestation && make ci-attestation-validate` -->

### 4. API / contract sync (if applicable)

- [ ] No API contract changes
- [ ] Backend schema/routes changed and frontend/generated clients updated in same PR
- [ ] Contract/Pact/schema tests updated for changed wire behavior

_If contract changed, list impacted endpoints/schemas and test updates:_

### 5. Impact on data pipeline & Q&A behavior

**Data scraping / ingestion:**
- [ ] No changes
- [ ] Changes to scraper behavior (URLs, loaders, rate limiting, Playwright usage, etc.)
- [ ] Changes to config files (`data/config/*.txt`, `data/urls.txt`)

**Vector storage / embeddings / Postgres:**
- [ ] No changes
- [ ] Changes to chunking or embedding generation
- [ ] Changes to Postgres schema or retrieval functions (e.g., `search_similar_documents`)
- [ ] Potential impact on `unique_content_source` deduplication

**Q&A engine / prompts / language handling:**
- [ ] No changes
- [ ] Changes to `/ask` endpoint logic or routing
- [ ] Changes to prompt templates (English/Spanish)
- [ ] Changes to source attribution or answer formatting

_If any box above is checked, briefly describe the expected impact and any migration or backfill steps needed:_

### 6. Docker & environment variables

**Docker / Compose:**
- [ ] No Docker changes
- [ ] Updated `docker-compose` configuration
- [ ] Updated Dockerfile(s)

**Environment variables:**
- [ ] No env var changes
- [ ] New env vars required
- [ ] Existing env vars changed or removed

_List any new or changed env vars (name + brief purpose):_
<!-- Canonical committed defaults must be updated in `.env.local.example` -->

_Deployment / runtime notes (if any):_
<!-- e.g., "Requires `.env` update in production and staging before deploy." -->

### 7. Dependencies & UV sync checklist

**Python dependencies (pyproject / uv):**
- [ ] No dependency changes
- [ ] `pyproject.toml` updated
- [ ] `uv.lock` or lockfile updated (if applicable)
- [ ] `uv sync` run locally after changes

_If dependencies changed, explain why and call out any version pinning or platform-specific notes:_

### 8. Breaking changes / migrations

- [ ] No breaking changes
- [ ] Breaking change (describe below)

_Describe any breaking changes, required DB migrations, or one-time scripts:_

### 9. Related issues / context

- Related issue(s): <!-- e.g., Closes #123, Relates to #456 -->
- Additional context or design notes (if any):

### 10. Checklist

- [ ] Code follows project style and guidelines
- [ ] Tests added/updated as needed
- [ ] Root cause fixed (no workaround-only patch)
- [ ] `make ci` passes from repo root
- [ ] Docs / comments updated where appropriate
- [ ] If env vars changed, `.env.local.example` updated
- [ ] Manual testing performed against running app(s) (if applicable)

<!--
Notes:
- Prefer `uv` for running tests and dev commands (e.g., `uv run pytest`).
- Use pytest markers (`unit`, `integration`, `db`, `api`, `ui`) to classify tests.
- When touching the data pipeline (scraper, vector loader, Postgres), be explicit about
  potential impacts on existing data and search behavior.
-->
