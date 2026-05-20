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

## UI journeys (v1 waiver)

UJ-001, UJ-002, and UJ-003 include browser UI steps in `docs/user-journeys.md`.
**v1 does not run Playwright/full UI E2E** (per `docs/test-plan.md`).

| Journey | API E2E module | UI coverage (v1) |
|---------|----------------|------------------|
| UJ-001 ChatRAG | `test_uj001_ask_stream.py` | Vitest: `apps/chat-rag-frontend/src/test/ChatPanel.test.tsx` |
| UJ-002 Ingest | `test_uj002_ingest_job.py` | Vitest: `apps/data-management-frontend/src/test/JobForm.test.tsx` |
| UJ-003 Delete | `test_uj003_corpus_delete.py` | API-only (admin list UI post-v1) |

Post-deploy browser E2E is tracked for a future milestone (roadmap / test-plan).

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
