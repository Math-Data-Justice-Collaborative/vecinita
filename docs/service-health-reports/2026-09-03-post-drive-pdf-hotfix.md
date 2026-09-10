# Service health — 2026-09-03 post Drive PDF NUL hotfix

[Corpus: feature-list.md §F59 §F76]
[Spec: docs/bug-reports/BUG-2026-09-03-drive-pdf-nul-body.md]
[Spec: docs/staging-runbook.md §H1–H3]
Session: `HF-scheduled-job-fail` · tip under investigation: `422d590` (main / #341)

## Scope

Post-deploy verify after promote [#341](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/341)
(Drive PDF octet-stream extract). Depth: **H0ci + H1–H3** (staging + prod) + Modal/write
logs for residual `DataError` / NUL. No live freshness enqueue (no corpus mutate).

## Verdict

| Layer | Result |
|-------|--------|
| Infra overall | **PASS** |
| Behavior overall | **PASS (prod)** / **WARN (staging retrieval)** |
| Overall | **PASS** for hotfix ship; staging RAG quality follow-up noted |

Remediation routing: **none** for Drive PDF NUL path (deployed; no post-deploy recurrence yet).
Staging zero-source asks → **data** (re-embed / score check), not this hotfix.

## Deploy tip

| Surface | Tip | Notes |
|---------|-----|-------|
| `origin/main` | `422d590` | Merge #341 |
| Prod Modal `vecinita-data-management` | **v16 @ `422d590`** | 2026-09-03 17:28 EDT |
| Staging Modal DM | **v21 @ `3d01af5`** | PR merge ref = `fda5655` into prior tip (includes fix) |
| Deploy Staging | [run 33806863688](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/33806863688) | success @ `fda5655` |
| Deploy Modal (prod) | [run 33808035365](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/33808035365) | success @ `422d590` |
| Deploy DigitalOcean | [run 33808166368](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/33808166368) | success @ `422d590` |

## H0ci

| Check | Result |
|-------|--------|
| CI on `main` @ `422d590` | **PASS** — [run 33807537609](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/33807537609) |
| Deploy preflight | **PASS** |

## H1 — liveness

| Target | Result |
|--------|--------|
| Staging ChatRAG `/health` | **PASS** — `postgres` / `modal_embed` / `modal_llm` = ok |
| Staging write `/health` | **PASS** (HTTP/1.1; one HTTP/2 framing flake on first try) |
| Prod ChatRAG `/health` | **PASS** — deps ok |
| Prod write `/health` | **PASS** |
| Prod Modal DM / embed / LLM `/health` | **PASS** (200) |

## H2 — DB

| Check | Result |
|-------|--------|
| Laptop → staging Postgres:25060 | **FAIL** — TCP timeout (local network) |
| App-side DB (via ChatRAG H1 `postgres=ok`) | **PASS** (proxy evidence) |

Treat direct H2 from this laptop as **N/A**; app connectivity is green.

## H3 — ask smoke

| Target | Result | Detail |
|--------|--------|--------|
| Prod `POST /api/v1/ask` pantry | **PASS** | `language=en`, **5 sources**, ~483 ms (after one 120s cold timeout) |
| Staging `POST /api/v1/ask` pantry | **WARN** | Answer present (`en`) but **0 sources** — no-context fallback (~362 ms) |
| Staging browse `GET /documents` | **PASS** | `total=95` |
| Staging browse `?q=pantry` | **WARN** | `total=0` (docs with pantry titles exist without query) |
| Prod browse | **PASS** | `total=119` |

CI `staging-smoke` on #341 also marked success (`.s.s`) — that suite accepts any non-empty
answer + `en`/`es`, so it does **not** catch zero-source / no-context.

## Hotfix residual (Drive PDF NUL)

| Check | Result |
|-------|--------|
| Prod write logs since redeploy (~21:32 UTC) | No `DataError` / NUL / `%PDF` upsert failures (health-only traffic) |
| Prod/staging Modal DM logs (~2h) | No freshness `POST /jobs` success wave; no NUL/`DataError` lines |
| Next schedule tick | ~16:00 EDT daily — **confirm then** that Drive freshness soft-fails or extracts text |

Code is live on prod Modal v16; behavioral proof for the incident path waits on the next
`freshness_refresh` wave (or an explicit staging-only Refresh now — AskQuestion if prod).

## Notes

- Prod `/warm` with wrong header returned 401; ChatRAG ask still succeeded (proxy via DO).
- Rifreeclinic remains `refresh_enabled=false` (expected soft-fail quarantine).

## Follow-ups

1. After next 16:00 freshness: scan Modal DM + write-api for `DataError` / Drive PDF.
2. Staging retrieval: investigate missing embeddings / score floor (95 docs browsable, 0 sources on ask).
3. Optional: tighten H3 smoke to require `sources` non-empty (or non-fallback answer).
