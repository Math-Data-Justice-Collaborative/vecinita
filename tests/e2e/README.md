# E2E tests (T0 local)

## Run commands

Workspace apps (`vecinita_chat_rag_backend`, etc.) are installed only in the **uv** virtualenv.
Do **not** use bare `pytest` from the system Python — imports will fail.

```bash
uv sync --group dev
uv run pytest tests/e2e/ -m "e2e and not live" -v
```

Or use the repo wrapper (syncs + runs pytest):

```bash
bash scripts/run_tests.sh tests/e2e/ -m "e2e and not live" -v
```

Full suite (matches CI):

```bash
bash scripts/run_tests.sh
```

## Tiers

| Tier | Marker | When |
|------|--------|------|
| T0 local | `e2e` and not `live` | TestClient + test DB; CI |
| T3 live | `e2e` and `live` | `VECINITA_STAGING_CHAT_URL` set; see `tests/smoke/test_staging_*.py` |

## UI journeys

| Journey | API E2E module | Vitest (component) | Playwright (T0-ui) |
|---------|----------------|--------------------|--------------------|
| UJ-001 ChatRAG | `test_uj001_ask_stream.py` | `ChatPanel.test.tsx` | `tests/ui/chat/uj001-chat-shell.spec.ts` |
| UJ-002 Ingest | `test_uj002_ingest_job.py` | `JobForm.test.tsx` | — (post-v1) |
| UJ-003 Delete | `test_uj003_corpus_delete.py` | API-only | — |
| UJ-009 Browse corpus | `test_uj009_corpus_browse.py` | Corpus tests | `tests/ui/chat/uj009-corpus-navigation.spec.ts` |
| UJ-026 Admin login | `test_uj028_unauthenticated_admin.py` | login tests | `tests/ui/admin/uj026-login-page.spec.ts` |

**T0-ui** runs in CI (`ui-e2e` job). **T3-ui** (live staging browser) is tracked for 13-deploy-smoke / H6.

## AC-C6 latency

| Environment | Test | Threshold |
|-------------|------|-----------|
| Local (mocked) | `test_uj001_mocked_ask_latency_informative` | &lt; 15s (sanity) |
| Staging (live) | `tests/smoke/test_staging_latency.py` | p95 &lt; 15s over 5 asks |

Run staging latency after deploy:

```bash
export VECINITA_STAGING_CHAT_URL=https://your-chat-backend.example
uv run pytest tests/smoke/test_staging_latency.py -m live -v
```
