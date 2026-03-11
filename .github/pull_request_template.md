## Summary
<!-- What does this PR do? One or two sentences. -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Data pipeline / scraper
- [ ] Prompt / LLM change
- [ ] Infra / Docker / DB schema
- [ ] Docs / config

## Related Issue
Closes #<!-- issue number -->

## Changes
<!--
List key files changed and why.
e.g.
- src/main.py: added caching to /ask endpoint
- src/utils/scraper_to_text.py: added retry logic
-->

## Testing
- [ ] `uv run pytest` passes locally
- [ ] Relevant unit/integration tests added or updated
- [ ] Tested `/ask` endpoint manually (if touching src/main.py)
- [ ] Data pipeline tested with `scripts/data_scrape_load.sh` (if touching scraper/vector loader)
- [ ] Playwright tests pass (if touching UI)

## RAG / Pipeline Checklist (if applicable)
- [ ] Chunking behavior unchanged or intentional (chunk size / overlap)
- [ ] Embedding model unchanged or migration path documented
- [ ] `unique_content_source` constraint respected (no duplicate inserts)
- [ ] Vector search threshold / match count reviewed
- [ ] Prompt templates updated for both EN and ES (if prompt change)

## DB / Schema Changes
- [ ] No schema changes
- [ ] Schema change included in `upgrade_schema.sql`
- [ ] Supabase RPC `search_similar_documents` signature unchanged

## Environment / Config
- [ ] No new env vars required
- [ ] New env vars added to `.env.example`
- [ ] `pyproject.toml` / `uv.lock` updated (if deps changed)

## Notes for Reviewer
<!-- Anything tricky, context on decisions, known limitations. -->