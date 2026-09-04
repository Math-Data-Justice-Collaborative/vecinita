# ADR-022: GPU Memory Snapshots for vLLM cold-start reduction

**Status:** Accepted (S001 P3 measured; **EV-313 / #313** re-enables **prod-only** — see Amendment below)
**Stage:** 00-context (S001-modal-cold-start-snapshot); amendment EV-313-prod-gpu-snapshots
**Date:** 2026-06-25; amended 2026-08-31

## Context

`vecinita-llm` (vLLM Qwen2.5-1.5B on T4, ADR-009) runs **scale-to-zero** to stay inside the
ADR-004 budget (≤$50/mo hard, ≤$25/mo target). The cost of that is cold starts: the first chat
question after idle measures **~68s and returns 504** (exceeds DigitalOcean's ~60s gateway),
versus **~14.6s warm** (BUG-2026-05-22, service-health 2026-05-21). The dominant cost is
`vllm.LLM(...)` initialization in `LlmService.load_model()`.

The obvious fix — `min_containers=1` (always warm) — is rejected: a T4 warm 24/7 ≈ **$430/mo**,
~9x the hard cap. We need to cut cold-start *latency* while keeping the container scaled to zero
when idle.

Modal **Memory Snapshots** (CPU + alpha GPU) serialize post-initialization container state so
later boots restore instead of re-initializing, claimed 3–10x init speedup — without keeping
containers warm. This preserves the scale-to-zero cost model.

## Decision

**Proposed:** Adopt **GPU Memory Snapshots** for `LlmService` to reduce cold start, **only if**
instrumentation (S001 Phase P1) confirms that library init + compilation (snapshot-able)
dominates the cold path rather than weight loading (not snapshot-able).

- `enable_memory_snapshot=True` + `experimental_options={"enable_gpu_snapshot": True}`.
- Split `@modal.enter` into `snap=True` (engine/graph build, warm-up, KV-cache discarded) and
  `snap=False` (per-restore reinit).
- Mitigations: `TORCHINDUCTOR_COMPILE_THREADS=1`, `XFORMERS_ENABLE_TRITON=1`, KV-cache
  discard/recreate per Modal's official vLLM example (`sleep(level=1)` / `wake_up()`),
  preserve existing `@modal.exit()` NCCL teardown.
- **vLLM pin:** `0.7.x` in Modal image (sleep mode API; was `0.6.x`).
- **A/B lever:** `VECINITA_LLM_ENFORCE_EAGER` env (default `true`; S001 T7) — staging keeps
  eager on until P3 traces confirm graph-capture + snapshot restore is faster.

This is a **spike with a kill switch**, not a committed design — GPU snapshots are alpha and
vLLM is explicitly flagged by Modal as needing rewrites.

## Decision gate

| Instrumentation result | Outcome |
|------------------------|---------|
| compilation/CUDA init > weight load | Proceed; this ADR moves to Accepted on measured win |
| weight load dominates | **Reject** snapshots (Modal: snapshots don't speed weight load and may add overhead); this ADR → Rejected; fall back to budget-safe combo |

> Note: vLLM has **no GA CPU-snapshot fallback** — `vllm.LLM(...)` initializes CUDA at
> construction, which a CPU-only `@modal.enter(snap=True)` cannot do, so `LlmService` depends on
> the **alpha** GPU snapshot. The "weight load dominates" branch therefore falls back to the
> budget-safe combo, not a CPU snapshot. Estimated weight load for Qwen2.5-1.5B fp16 (~3 GB at
> ~1–2 GB/s) is only ~2–3s, so the gate is expected to pass.

## Alternatives considered

| Alternative | Why not (default) |
|-------------|-------------------|
| `min_containers=1` always warm | ~$430/mo — violates ADR-004 |
| `buffer_containers` | Does nothing when scaling *from* zero (Modal cold-start guide); useless for our idle→cold pattern |
| Scheduled / peak-hours warming | Still meaningful cost; keep as a cost-bounded demo dial (S001 T13), not primary |
| `enforce_eager=True` only | Cheap, ships regardless (S001 T10); smaller ceiling than snapshots |
| Smaller / quantized model | Marginal; weight load isn't confirmed bottleneck; quant kernels add compile |
| Ollama fallback (ADR-009) | Larger change; revisit only if vLLM path can't meet budget+latency |

> **Primary lever runs in parallel, not as an alternative:** pre-warm on session open (S001
> T11) overlaps the boot with user think-time and defeats the DO 504 *regardless* of whether
> this snapshot spike passes its P1 gate. Per Modal's cold-start guide, `@modal.enter` only
> *moves* latency into the warm-up period — pre-warm is what hides that period from the user, so
> it leads the S001 priority order and ships independent of this ADR's outcome.

## Consequences

- **If accepted:** cold start drops without raising idle cost; scale-to-zero preserved. Adds
  alpha-feature risk and vLLM-specific init complexity; snapshots recapture on every deploy and
  across worker types (2–3 captures per GPU).
- **If rejected:** budget-safe combo (T10) still improves cold-start UX; revisit when GPU
  snapshot leaves alpha or model/GPU tier changes.
- Cold-start latency remains excluded from the p95 < 15s target (RD-017) but must be documented
  for ops either way.

## Amendment — EV-313 / #313 (2026-08-31)

**Trigger:** After ADR-037, prod `LlmService` left `enable_memory_snapshot=False` because
playground-style **model_id reload** broke NCCL. ADR-037 isolated playground on
`vecinita-llm-playground`; **prod is pinned** (`allow_model_reload=False`). The reload
rationale no longer applies to production topology, but the flag was never restored.

**Decision (amended):**

1. **Prod `vecinita-llm` only:** Re-enable GPU memory snapshots behind kill-switch
   `VECINITA_LLM_GPU_SNAPSHOT` (`true`/`false`; **unset = false** until staging evidence).
   The value is read at **`modal deploy` import time** and baked into
   `enable_memory_snapshot` + enter hooks — set it in the **deploy shell**, then redeploy
   (Modal container Secrets alone do not flip the flag). Wire GPU snapshot experimental
   options when the switch is on.
2. **Lifecycle:** `@modal.enter(snap=True)` — load pinned Qwen, warm (tiny + RAG-sized),
   vLLM **Level-1 sleep** (weights retained, KV discarded), capture.
   `@modal.enter(snap=False)` — **wake_up**, then resolve/verify promoted LoRA (**base
   snapshot only**; do not bake mutable adapters Volume into the snapshot — Volume
   mutations do **not** invalidate Modal snapshots; see #316 / ADR-053).
3. **Playground:** Remains `enable_memory_snapshot=False` (reload allowed).
4. **SLO honesty:** Do not claim ubiquitous sub-second cold-from-zero until re-measured.
   Planning frontier from #311 research: direct restore **p50 ~1–2s / p95 ~3–10s** until
   staging proves Green (`p50 <1s`, `p95 <3s`). Ship **Useful** band with documented
   frontier if Green unmet; **Red** → disable switch and consider Plan B (custom CPU
   driver) only then.
5. **Out of this amendment:** always-on T4, playground snapshots, FE prewarm / ASGI thin
   ingress / scaledown tune / FAQ bypass (sibling #311 children).
6. **Prod cutover:** Staging evidence first; live prod enable requires AskQuestion
   (`no-live-prod-corpus-push` does not apply to LLM config, but prod latency cutover
   still needs explicit approve).

**Cutover log (EV-313 / 2026-08-31):**

| Environment | `VECINITA_LLM_GPU_SNAPSHOT` | Evidence |
|-------------|----------------------------|----------|
| Modal `staging` | `true` (deploy shell) | TC-313-02: `Restoring Function from memory snapshot.`; H1 + warm H3 PASS |
| Modal `main` (prod) | `true` (deploy shell; AskQuestion approve) | Create + restore log lines; `/health` `/warm` `/generate` PASS |

Playground remains snapshot-off. Flag is **not** stored in Modal Secrets — re-deploy with the
env set after any CD that omits it.

### Amendment EV-316 — LoRA after restore (integrity)

**Problem:** Modal Volume mutations do **not** invalidate Memory Snapshots. Baking a promoted
LoRA into the snapshot risks silently serving a stale adapter after promote/rollback.

**Decision (EV-316 / #316):**

1. **Base snapshot only** — `snap=True` loads pinned Qwen with LoRA *capacity* but **no**
   promoted adapter weights from the mutable volume.
2. **Post-restore resolve (default)** — `snap=False` → `wake_up` → bind current
   `VECINITA_FINETUNE_ADAPTER_ID` from volume, then verify integrity.
3. **Integrity algorithm: SHA-256** (`hashlib.sha256`) over a canonical adapter-dir digest
   (sorted relative paths; each file contributes `path ‖ NUL ‖ size ‖ NUL ‖ bytes`). Reject
   symlinks that escape the adapter root. Compare expected
   `VECINITA_FINETUNE_ADAPTER_HASH` (lowercase hex) with `hmac.compare_digest`. **Do not** use
   MD5, SHA-1, or CRC for the authoritative pin.
4. **Fail closed** — missing dir, hash mismatch, or hash set without id → raise before ready;
   do not serve generate claiming the wrong adapter.
5. **Ready metadata** on prod `GET /health`: `base_model_id`, `adapter_id`, `adapter_hash`,
   `snapshot_schema`, `git_commit` (plus `status`).
6. **Kill-switch** `VECINITA_LLM_LORA_RESOLVE`: `post_restore` (default) \| `snapshot_bound`
   (legacy/debug only; not recommended when volumes mutate). Independent of
   `VECINITA_LLM_GPU_SNAPSHOT` and `VECINITA_LLM_ENFORCE_EAGER`.
7. **Tests:** TC-316-01 (promote-matrix stale-adapter), TC-316-02 (ready + hash fail-closed);
   AC-FT11.

**Kill switches (independent):** `VECINITA_LLM_GPU_SNAPSHOT`, `VECINITA_LLM_ENFORCE_EAGER`,
`VECINITA_LLM_LORA_RESOLVE`.

### Amendment EV-314 — Layer E latency harness (#314)

**Problem:** Without `cold_kind`-tagged samples and enough restores for tails, restore/create
baselines and DO-504 regression gates stay anecdotal (S001 n≈3–6; TC-313 smoke).

**Decision (EV-314 / #314):**

1. Modal LLM emits structured stamps (restore → wake → adapter ready → first token) with
   ADR-004 allow-listed tags: `cold_kind ∈ {warm, snapshot_restore, snapshot_create,
   clean_boot}`, worker type, commit, snapshot config, base/adapter ids — **no raw prompts**.
2. Opt-in `scripts/ops/cold_start_bench.py` (name finalized in tech-plan): forced cold via
   documented `modal container stop`; staged **N≈20** smoke then **≥100** for publishable p95.
3. ChatRAG DO-receive stamp and F84 cold_kind dimensions are **deferred**.
4. Do not conflate `#318` `prewarm_to_ready` with cold TTFT / restore samples.
5. 15-service-health may cite the script; MUST NOT run N=100 inside the skill by default.

### Amendment EV-318 — Async GPU prewarm (#318)

**Problem:** LLM `POST /warm` awaited `warm_model.remote.aio`, holding ASGI during GPU boot
(embedding already uses `.spawn()`). Health-only probes never boot the T4.

**Decision (EV-318 / #318):**

1. Prod LLM ASGI `/warm` **spawns/detaches** and returns promptly (mirror embedding).
2. ChatRAG `POST /api/v1/warm` remains the FE mount prewarm contract (not `/health`).
3. Predictors this cycle: **mount only**; F40/F64 residual wait UX kept.
4. Instrument `prewarm_to_ready` via structured logs/harness tags; F84 dimensions deferred.
5. Playground blocking warm may remain for eval ready semantics this cycle.

### Amendment EV-315 — Seed GPU snapshots after deploy (#315)

**Problem:** Snapshot **creation** can take ~70s; Modal may need 2–3 captures per worker
type. Without a post-deploy prime, the first real user can pay create instead of restore.

**Decision (EV-315 / #315):**

1. After staging LLM deploy, run opt-in `scripts/ops/seed_gpu_snapshots.py` (or equivalent)
   that authenticates to Modal `POST /warm` and loops until observed samples are
   `cold_kind=snapshot_restore` (via #314 stamps/logs) — **fail closed** if create remains.
2. Document create latency separately from restore percentiles.
3. Staging: script + runbook this cycle; optional advisory CI only — **not** a hard CD gate.
4. Prod prime requires AskQuestion; default Environment is staging.
5. Do not conflate seed primes with FE mount `prewarm_to_ready` (#318).

### Amendment EV-317 — Thin Modal CPU ingress (#317)

**Problem:** Cold path can still pay heavy ASGI import/boot in series with GPU restore.
Health must never allocate T4.

**Decision (EV-317 / #317):**

1. Lazy-import / thin ASGI entry so vLLM and heavy GPU internals are **not** imported at
   ASGI module load (S001 T12).
2. Prefer same image + lazy imports before introducing a second Modal image.
3. Keep ASGI on **CPU**; preserve `/warm` `.spawn()` (#318).
4. Optional CPU `enable_memory_snapshot` on ingress **only if** post-thin profiling still
   shows material ASGI boot cost.
5. Unit/AST tests guard against top-level vLLM import on the ASGI entry module.

### Amendment EV-319 — Cost-tune `scaledown_window` (#319)

**Problem:** Hardcoded `scaledown_window=300` can dominate idle T4 cost at pilot traffic.
`buffer_containers` does not fix scale-from-zero; always-on is out of scope.

**Decision (EV-319 / #319):**

1. Document T4 $/s idle formula and monthly idle-tail estimate under ADR-004.
2. Candidates **60 / 120 / 300** s; prefer **120** as first flip when staging gap data is
   thin (timestamp-only histogram; no prompts/PII).
3. Deploy-time env `VECINITA_LLM_SCALEDOWN_WINDOW` (validated int; invalid → fail closed);
   easy revert to `300`.
4. Leave `buffer_containers=0`; do **not** add `min_containers` in this ticket.
5. Prod default change requires AskQuestion after staging evidence.

### Amendment EV-320 — Layer D FAQ fast-path (#320 / #79 / F85)

**Problem:** True cold-from-zero GPU TTFT cannot be ubiquitous sub-second under ADR-004.
High-confidence **reviewed** FAQs can skip T4 entirely for a subset of asks.

**Decision (EV-320 / #320 / F85):**

1. **ChatRAG-side bypass** before retrieve/LLM when an exact/normalized **same-language**
   FAQ variant matches a versioned reviewed store (YAML/JSON). Prefer miss over wrong answer —
   **no** embedding/semantic FAQ similarity this cycle.
2. Response metadata: `answer_path ∈ {faq_bypass, rag_llm}` on ask/stream. **Do not** overload
   GPU `cold_kind` (`warm` / `snapshot_restore` / `snapshot_create` / `clean_boot`) — FAQ is not
   a cold-start kind. Harness may classify `faq_bypass` via `answer_path` for Layer E dashboards
   (`validate_answer_path_latency_sample` + `cold_start_bench.py --mode chat-ask`; TC-320-05 /
   AC-320-05).
3. On bypass: `sources=[]`, `cache_hit=none` (distinct from F43), **$0 GPU** (no Modal generate).
4. Kill-switch `VECINITA_FAQ_FASTPATH_ENABLED` (default **true**); store path
   `VECINITA_FAQ_STORE_PATH` optional override.
5. Admin hot-load editor (#81) and full query-router umbrella (#76) remain out of scope.
6. Naming: GitHub **#79** ≠ product **F79** (freshness).
7. Sibling ops (seed #315 / scaledown #319) stay AskQuestion-gated for prod; staging execute
   after Build gate with `.env` creds.

**Tests / AC:** TC-320-01–05 · AC-320-01–05 · UJ-093.

### Amendment EV-311 — Umbrella close on evidence (#311)

**Problem:** Child slices shipped (#313/#314/#316/#318/#320) but parent #311 still open without
a published restore frontier vs the original SLO table. Remaining children (#315 seed,
#317 thin ingress, #319 scaledown) stay `priority:medium` backlog.

**Decision (EV-311 / #311 — 2026-09-04):**

1. **Close the umbrella on evidence**, not by implementing medium children in this cycle.
2. **Staging only** for forced-cold bench (`modal container stop` + `scripts/ops/cold_start_bench.py`).
   Cite EV-313 prod cutover; do **not** run prod `container stop` without a separate AskQuestion.
3. **Harness:** `generate` mode + `--force-cold`; smoke **N≈20** (TC-314-02 / TC-311-01). Optional
   **N≥100** for publishable p95 when smoke looks Good — not required to close if Useful band
   is documented honestly.
4. **E2E:** One staging ChatRAG ask path (`chat-ask` mode and/or H3) — no silent 504; record
   latency separately from Modal restore percentiles.
5. **SLO bands (unchanged honesty):**
   - **Green:** restore p50 &lt; 1s and p95 &lt; 3s (direct Modal `/generate`).
   - **Useful:** publish measured frontier (expect ~1–2s p50 / ~3–10s p95 until Green); keep
     snapshots on; close #311 with ADR frontier table filled from session evidence.
   - **Red:** restore worse than Useful planning band or DO 504 returns → do **not** close #311;
     disable/investigate `VECINITA_LLM_GPU_SNAPSHOT` before claiming success.
6. **Docs:** Fill frontier numbers in this amendment + staging-runbook §EV-311 + session research
   note under pack session `reports/`. Point `infra/modal/README.md` at the close procedure.
7. **Defer:** #315 / #317 / #319 remain open backlog; do not block #311 close.

**Tests / AC:** TC-311-01 · TC-311-02 · AC-311-01–04.

**Frontier table (fill after Build evidence):**

| Metric | Target (Green) | Measured (staging) | Band |
|--------|----------------|--------------------|------|
| Restore p50 (`snapshot_restore`) | &lt; 1s | **~44s** (n=5 timed `/generate` after force-cold; 2026-09-04; snapshots re-enabled) | **Red** |
| Restore p95 | &lt; 3s | **~72s** max in same n=5 (not publishable p95; N&lt;100) | **Red** |
| E2E cold ask (ChatRAG) | p50 &lt; 2s when restore hot; never silent 504 | FAQ path p50 **~226ms** (n=5); RAG-after-cold TBD (post-stop InternalFailure common) | FAQ Useful; restore E2E incomplete |
| Warm ask | no regression | ~1s Modal `/generate` when container hot | OK |
| N / date / commit | — | n=5 restore curls + FAQ bench; 2026-09-04; harness force-cold fix on `evolve/EV-311-cold-start-latency` | — |

**Umbrella close:** **blocked** (Red restore). Keep #311 open; ship harness CLI fix; pursue #315/#317 + snapshot efficacy.
## References

- S001 plan: `docs/sessions/S001-modal-cold-start-snapshot/cold-start-spike-plan.md`
- Modal Memory Snapshots: https://modal.com/docs/guide/memory-snapshots
- Modal cold start: https://modal.com/docs/guide/cold-start
- ADR-004 (cost/sovereignty), ADR-009 (vLLM on T4), ADR-037 (prod pin / playground),
  ADR-053 (LoRA promote)
- BUG-2026-05-22 (cold-start UX), `docs/sessions/S000-internal-docs-archive/reference.md#cost-monitoring-baseline-adr-004`
- Parent latency system: GitHub #311; slices: #313, #316, #314, #318, #315, #317, #319, #320
- Session: `EV-313-prod-gpu-snapshots`; `EV-316-lora-post-restore`;
  `EV-314-cold-start-latency-harness`; `EV-318-async-gpu-prewarm`;
  `EV-315-seed-gpu-snapshots`; `EV-317-thin-cpu-ingress`; `EV-319-scaledown-window`;
  `EV-311-infra-sub-second-chatrag-latency-on-cheap-server` (umbrella close)
  (pack session store)
