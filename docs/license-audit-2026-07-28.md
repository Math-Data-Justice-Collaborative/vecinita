# License audit — 2026-07-28

**Scope:** full recursive lockfile tree + weights/data assets + SPDX SBOM  
**Verdict:** **FAILED** — BLOCKED non-commercial (NC) playground model  
**Engineering assessment only** — not legal advice.

## Executive summary

| Metric | Count |
|--------|------:|
| Packages audited (Python + npm) | ~558 |
| Model / data assets | 16+ |
| BLOCKED (NC) | 4 catalog tags → Qwen2.5-3B Research License |
| FLAG | ~20 (first-party UNLICENSED/UNKNOWN, gated Llama/Gemma, custom EULAs, SBOM phantoms) |
| COPYLEFT (weak) | `psycopg`, `psycopg-binary`, `psycopg2-binary` (LGPL) |
| PyRosetta | **none** |

**Prod pin** `Qwen/Qwen2.5-1.5B-Instruct` is **Apache-2.0** (commercial OK).  
**Playground catalog** still lists `qwen2.5:3b-*` → `Qwen/Qwen2.5-3B-Instruct` under **Qwen Research License (NC)** — **BLOCKED**.

Package trees are largely OSI / commercial-friendly. Audit fails on NC weights, not on npm/PyPI NC SPDX.

## BLOCKED — Non-commercial-only (NC)

| Asset | Where | License | Remediation |
|-------|-------|---------|-------------|
| `Qwen/Qwen2.5-3B-Instruct` | Playground catalog / `resolve_hf_repo` | Qwen RESEARCH LICENSE — non-commercial / research-only | Remove or hard-gate until commercial grant |
| `qwen2.5:3b-instruct` | `packages/shared-schemas/.../playground_catalog.py` | same | same |
| `qwen2.5:3b-instruct-q4_K_M` | same | same | same |
| `qwen2.5:3b-instruct-q8_0` | same | same | same |

No `CC-BY-NC-*` / `PolyForm-Noncommercial-*` packages in npm or Python trees. No PyRosetta.

## SBOM status (updated in-session)

At audit start, Microsoft `sbom-tool` emitted **420/420** `NOASSERTION` licenses (flags `-li`/`-pm` were not passed; ClearlyDefined bulk also returned 524).

**Follow-up applied the same day:**

- `scripts/security/run-all.sh` enables `-li true`, `-pm true`, and `enrich_sbom_licenses.py`
- Post-enrichment: **411/420** SPDX packages have concrete licenses (mostly MIT / Apache-2.0 / ISC / BSD)
- Remaining 9 `NOASSERTION`: first-party apps + SBOM phantoms (`@my-scope/*`, `ljharb-monorepo-symlink-test`) + root
- Python inventory: `.security-reports/sbom/python-licenses.json` (**131/143** resolved; 12 first-party `vecinita-*`)

**Python gap:** UvLock detections are still dropped from the emitted SPDX package list; use `python-licenses.json` / this audit for PyPI.

## Notable FLAG / COPYLEFT

| Item | Tier | Notes |
|------|------|-------|
| First-party `vecinita-*` (Python/npm) | FLAG | UNKNOWN / UNLICENSED — add LICENSE/NOTICE if shipping OSS |
| `Qwen/Qwen2.5-72B-Instruct` | FLAG | Custom Qwen license (not NC; MAU clause) — not default catalog |
| Llama / Gemma registry aliases | FLAG | Gated community licenses |
| Modal / NVIDIA CUDA runtime | FLAG | Infra EULA — accept as runtime |
| `psycopg*` / `psycopg2-binary` | COPYLEFT | LGPL — typical dynamic link for SaaS; counsel if redistributing binaries |
| `lightningcss*` | COPYLEFT | MPL-2.0 (npm) |

## Weights / data (selected)

| Asset | License | Tier |
|-------|---------|------|
| D6 `BAAI/bge-small-en-v1.5` | MIT | OK |
| D7 prod `Qwen2.5-1.5B-Instruct` | Apache-2.0 | OK |
| Playground Qwen2.5 0.5B/1.5B/7B/14B/32B | Apache-2.0 | OK |
| Playground **Qwen2.5-3B** (+ quant tags) | Qwen Research (NC) | **BLOCKED** |
| Seed fixtures D1–D5, D8–D11 | first-party / synthetic | OK* / FLAG (UNLICENSED frontends) |

## Drift

- Playground Qwen2.5-3B NC not documented in dependency inventory / data-management plan
- D7 LLM weights referenced in DMP matrix but missing from asset inventory table
- Pre-trained Models / Weights table incomplete in `docs/dependency-inventory.md`

## Recommendations

1. **Required:** remove or hard-gate `qwen2.5:3b-*` from `PLAYGROUND_MODEL_CATALOG` / `resolve_hf_repo` before commercial deploy.
2. Document D6/D7 + playground HF repos (with SPDX/terms) in inventory + DMP.
3. Keep SBOM license enricher in `make security-scan`; optional CI deny-list for `NC|Non-Commercial|qwen-research`.
4. Add root / package LICENSE or proprietary NOTICE for first-party UNKNOWN/UNLICENSED flags.
5. Counsel for LGPL `psycopg*` redistribution, Modal/NVIDIA runtime, any Llama/Gemma pulls.

## References

- Auditor: license-researcher (2026-07-28)
- SBOM fix: `scripts/security/run-all.sh`, `scripts/security/enrich_sbom_licenses.py`, `docs/security/static-analysis.md`
- Catalog: `packages/shared-schemas/vecinita_shared_schemas/playground_catalog.py`

## Remediation (2026-07-29)

**ISS-004 closed:** Removed `qwen2.5:3b-*` from `PLAYGROUND_MODEL_CATALOG`; `resolve_hf_repo` raises on `Qwen/Qwen2.5-3B-Instruct`; catalog family tags filter via `resolve_hf_repo` (RD-168). Prod pin 1.5B Apache-2.0 unchanged.
