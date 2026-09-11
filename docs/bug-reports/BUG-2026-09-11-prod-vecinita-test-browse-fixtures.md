# BUG-2026-09-11 — Prod corpus browse shows `*.vecinita.test` fixtures

> **Status:** classifier fixed in working tree; **prod delete pending AskQuestion**  
> **Date:** 2026-09-11  
> **Component:** ChatRAG browse (`GET /api/v1/documents`); corpus cleanup classifier  
> **Session:** EV-stage-prod-validation-e2e  
> **Corpus:** [Corpus: corpus-db-safety] [Corpus: no-live-prod-corpus-push]
> [Spec: .cursor/rules/no-corpus-test-artifacts.mdc]

## Error description

Production Corpus browse (APP + API) surfaces synthetic browse fixtures at the top
of the document list:

- `https://browse-housing.vecinita.test/` — “Housing help center”
- `https://browse-legal.vecinita.test/` — “Legal Aid clinic”

These came from integration/e2e seeds (`tests/integration/test_browse_api.py`,
`tests/e2e/test_uj009_corpus_browse.py`) that used `*.vecinita.test` hosts. The
cleanup classifier only matched `example.com` / `fixture://` / localhost, so
operator cleanup missed them.

Staging browse (95 docs) had **no** `*.vecinita.test` leftovers in this pass.

## Error logs

```text
GET https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app/api/v1/documents?page=1&page_size=3
→ items[0].url = https://browse-housing.vecinita.test/
→ items[1].url = https://browse-legal.vecinita.test/
→ total = 97

Prod APP /corpus: list starts with “Housing help center”, “Legal Aid clinic”
```

## Investigation

| Hyp | Result |
|-----|--------|
| Classifier misses `vecinita.test` | **Confirmed** — `is_corpus_test_artifact_url` returned False |
| Stage polluted too | **Not found** in first 95 docs |
| Live ask broken by fixtures | **No** — ask/stream returns real community sources |

## Fix

1. **Code (done, uncommitted):** extend classifier + SQL predicate for `*.vecinita.test`;
   migrate browse fixtures to `*.example.com`; update
   `.cursor/rules/no-corpus-test-artifacts.mdc`.
2. **Ops (blocked on AskQuestion):** dry-run then `--apply` cleanup against **prod**
   corpus DB (requires prod `DATABASE_URL` + corpus-reset ack). No prod DB URL in
   `.env` this session — operator must supply.

## Repro test

- `tests/unit/test_corpus_test_artifacts.py` — RED then GREEN for `*.vecinita.test`
- Live browse evidence: session `evidence/live-2026-09-11/prod/h3b_docs.json`
