# EV-023 — Vecinita plugin migration decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-24 | Archive numbered `00–19` + `pipeline` | Plugin orchestrators + `spec-*` / `build-*` |
| 2026-08-24 | Archive pack duplicates (github-projects, doc-planner, …) | Plugin `support-*` and spec skills |
| 2026-08-24 | Archive alternate pipeline skills (build-planner, build-executor, …) | Plugin `spec-tech-plan`, `build-build`, etc. |
| 2026-08-24 | Keep corpus/Modal/RAG project skills | Vecinita-specific domain content |
| 2026-08-24 | New sessions → `~/.cursor/workflow/{owner}/vecinita/sessions/` | Pack session-store-path; EM project id `vecinita` |
| 2026-08-24 | `workflow-state.yaml` retained for brownfield in-flight only | EV-027 and similar legacy sessions |

[Corpus: skill-placement]
