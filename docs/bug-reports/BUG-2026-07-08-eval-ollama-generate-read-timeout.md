# BUG-2026-07-08 — Golden eval fails: "The read operation timed out" (Ollama generate)

**Status:** verifying (fix applied locally; local-first — deploy pending user approval)
**Severity:** high — golden batch eval blocked for larger models
**Feature:** F36 / F37 / F38 eval playground (ADR-035, EV-009/EV-010)
**Reported:** 2026-07-08
**Environment:** admin frontend → internal-write-api (DO) → Modal `vecinita-ollama`

## Error description

Running a golden batch evaluation against a `qwen3` Ollama tag fails with:

```
Evaluation run failed: The read operation timed out
```

The eval run is marked `failed` and `error_message` is set to the read-timeout string. The
default model `qwen2.5:1.5b-instruct` is small enough to sometimes complete, but a larger
`qwen3` tag reliably times out.

## Error logs

User-facing:

```text
Evaluation run failed: The read operation timed out
```

Live Modal logs — `modal app logs vecinita-ollama` (2026-07-08):

```text
    POST /warm -> 404 Not Found  (duration: 191.4 ms, execution: 76.5 ms)
Task's current input(s) ["in-01KX0YNZCTW5FN87C71FK5CEAH:..."] cancelled because:
    Task's current input ... hit its timeout of 120s
[modal-client] Received a cancellation signal while processing input (...)
Task exception was never retrieved
future: <Task finished ... exception=RemoteDisconnected('Remote end closed connection without response')>
Traceback (most recent call last):
  ...
  File "/root/ollama_app.py", line 365, in generate
    text = _ollama_generate_text(...)
  File "/root/ollama_app.py", line 176, in _ollama_generate_text
    body = _read_generate_body()
  File "/root/ollama_app.py", line 168, in _read_generate_body
    with urllib_request.urlopen(req, timeout=600) as response:
  ...
  File "/usr/local/lib/python3.11/http/client.py", line 294, in _read_status
    raise RemoteDisconnected("Remote end closed connection without response")
http.client.RemoteDisconnected: Remote end closed connection without response
Input in-...:... failed to respond to cancellation for too long: 30 seconds - killing task
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Performance / timeout — eval run failed |
| Where | Production (admin frontend → internal-write-api → Modal) |
| When | Running a golden batch eval with a `qwen3` model tag |
| Frequency | Every time for larger models; intermittent/OK for `qwen2.5:1.5b-instruct` |
| Repro env | Production; also reproducible as a static config invariant locally |
| Severity | High — golden eval blocked for the chosen model |
| Evidence | User report + live `vecinita-ollama` Modal logs (above) |
| Tried | Nothing |
| Model tag | A `qwen3` tag pulled via the F38 playground download UI |

## Remediation path

**local-first / investigate-only** — user selected *Investigate only for now: write BUG
report + repro test, no code/deploy yet*. Deploy intent (when fixed) = **local-first**.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Golden batch eval with a `qwen3` tag completes instead of failing with a read timeout |
| Verification checks | Full main CI parity (local) + GitHub CI; repro test red→green; (deploy layers deferred until fix approved) |
| Monitoring | User re-runs golden eval in admin after any future deploy |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Client-side read timeout produces the literal message | **Confirmed** — `LlmClient` uses `httpx.Client(timeout=120.0)`; `str(httpx.ReadTimeout)` == `"The read operation timed out"`. Eval builds the Ollama client via `_ollama_llm_client()` with no timeout override, so it inherits the 120s default (`packages/llm-client/vecinita_llm_client/client.py:36,48`; `packages/eval/vecinita_eval/modal_llm.py:121-128`). |
| H2 | Modal `ollama_api` function timeout is shorter than its own inner inference read | **Confirmed (primary)** — `ollama_api` is decorated `timeout=120` (`infra/modal/ollama_app.py:293`) while `_ollama_generate_text` reads with `urlopen(req, timeout=600)` (`:168,:226`). The function is cancelled at 120s while still blocked in `getresponse()`. Live log: `hit its timeout of 120s`. |
| H3 | CPU-only inference makes first-token latency huge | **Confirmed (aggravating)** — none of `ollama_api`, `pull_model_job`, `stage_default_model` pass a `gpu=` argument, so Ollama runs CPU-only. A `qwen3` model load + first generation on CPU easily exceeds 120s. |
| H4 | `warm()` doesn't preload the model | **Confirmed (aggravating)** — eval calls `client.warm()` (`modal_llm.py:37-40`), but `vecinita-ollama` exposes no `/warm` route (`ollama_app.py:401-408`) → `POST /warm -> 404`, so nothing preloads and the first `/generate` eats the full cold-start + model load. |
| H5 | Inline `ollama pull` on 404 inside `/generate` blows the timeout | **Possible (secondary)** — on HTTP 404, `_ollama_generate_text` runs `_run_ollama_pull` inline (`:181`); pulling a multi-GB `qwen3` tag cannot finish inside the 120s function timeout. |
| H6 | DO wiring / secrets misconfigured | **Rejected** — `doctl` shows `internal-write-api` has `VECINITA_MODAL_OLLAMA_URL` + `VECINITA_MODAL_PROXY_KEY`; the request reached Ollama (got a 120s timeout, not 401/404). |

**Related bugs:** BUG-2026-07-06 (pull 503 / missing Modal app), BUG-2026-07-07 (generate 404 /
model not staged). Distinct symptom here: successful routing + reachable model, but generation
exceeds the 120s ceilings.

## Root cause

**Config/infra mismatch (multi-layer timeout collision + CPU inference).** The `vecinita-ollama`
`ollama_api` Modal function is capped at `timeout=120s` — shorter than its own inner Ollama read
(`urlopen(..., timeout=600)`) — so Modal cancels the task mid-generation and closes the socket.
Simultaneously, the eval-side `LlmClient` uses a 120s httpx read timeout, surfacing
`httpx.ReadTimeout` whose string is exactly `"The read operation timed out"`. Because Ollama runs
**CPU-only** and `warm()` 404s (no preload), the first golden-batch generation for a larger `qwen3`
model routinely exceeds both 120s ceilings.

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/feature-list.md` — F37/F38 eval playground with selectable models | In scope — the download UI lets a user pick a model that the runtime cannot serve within limits |
| `docs/deployment-integration.md` — `vecinita-ollama` GPU/timeout expectations | To verify during fix — confirm whether GPU + timeout are specified; note drift if so |
| `docs/config-spec.md` — eval `max_tokens` (default 256, max 1024) | Pass — token cap is not the primary driver; latency ceiling is |
| `docs/api-contract.md` — eval error shape | Pass — failure is recorded as `status=failed` + `error_message` |

*(Blocking spec cross-check to be completed in Phase 1.5 before any fix is triaged.)*

## Repro test

- `tests/bugs/test_bug_2026_07_08_eval_ollama_generate_read_timeout.py` — RED → **GREEN** (2026-07-08)
  - `test_ollama_api_function_timeout_covers_inner_generate_read_timeout` — Modal function
    `timeout` must be >= the inner `urlopen` read timeout (was 120 < 600; now 900 >= 600).
  - `test_eval_ollama_client_read_timeout_tolerates_slow_generation` — the eval construction
    path (`_ollama_llm_client`) must use a read timeout above the 120s default that emits the
    exact `"The read operation timed out"` message (now 900).

## TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-08 | Added repro tests (function-timeout invariant + client-timeout invariant) | RED (expected) |
| 2 | 2026-07-08 | GPU + timeout=900 + `/warm` on `ollama_api`; eval-scoped 900s client timeout | GREEN |
| 3 | 2026-07-08 | Refined client test to the eval-scoped `_ollama_llm_client` path (fix is eval-scoped, not global default) | GREEN |

## Fix

Approved levers (user, 2026-07-08) + Modal best practices (cold-start, memory-snapshots,
high-performance LLM inference guides):

1. **`infra/modal/ollama_app.py`**
   - `ollama_api` now runs on **`gpu="T4"`** (biggest correctness win — CPU Ollama was the root slowness).
   - **`timeout=900`** (≥ inner Ollama read timeout 600) so Modal no longer cancels generation mid-read.
   - **`scaledown_window=300`** keeps a warm GPU container across a golden batch (still scale-to-zero when idle).
   - `ollama serve` started during container **warm-up** (init), not on the first served request.
   - New **`POST /warm`** route + `_preload_model()` load the requested model into VRAM before a batch.
   - Refactor: request models + `_authorized` + `_register_pending_model` hoisted to module scope.
   - Decision: GPU memory snapshots **not** used (external Ollama subprocess; snapshots don't speed
     up Volume weight loads — documented in module docstring).
2. **`packages/eval/vecinita_eval/modal_llm.py`** — eval `LlmClient` built with `_EVAL_LLM_TIMEOUT_S`
   (**900s**), scoped to eval only (Ollama path + vecinita-llm fallback). Global default stays 120s.
3. **`packages/llm-client/vecinita_llm_client/client.py`** — `warm()` sends `model_id` (Ollama) and
   uses the client's configured timeout so eval can wait for a first-load preload.
4. Pull jobs (`pull_model_job`, `stage_default_model`) intentionally stay CPU (download-only).

Spec back-add: `docs/deployment-integration.md` (§EV-010 runtime), `docs/config-spec.md`
(eval LLM read timeout).

## Verification

### Layer 1 — Automated

- [x] Repro test written and **red** for the right reason
- [x] Fix applied → repro test **green** (2 tests)
- [x] Related suite green: ollama app/manifest, llm-client, eval unit, eval_service, ollama clients (88 tests)
- [x] Pydantic field-metadata guard green; `infra.modal.ollama_app` import smoke OK
- [x] Ruff + basedpyright clean on all changed files
- [ ] Full CI parity (local) — before PR

### Layer 2–4

- [ ] Layer 2 — User re-runs golden eval with the `qwen3` tag (post-deploy; production-only latency)
- [ ] Layer 3 — Pre-deploy: `modal deploy infra/modal/ollama_app.py`; `/warm` + `/generate` smoke
- [ ] Layer 4 — Production verified after deploy (deferred until user approves deploy)

## Prevention & countermeasures

*(Pending Phase 5 prevention interview — after user confirms fix + deploy path.)*
