# Hotfix Log

| # | Date | Type | Summary | Bug report | Branch | Commit | Deployed | Verified |
|---|------|------|---------|------------|--------|--------|----------|----------|
| 1 | 2026-05-20 | Code bug | vLLM Modal shutdown + fp16 kwargs (NCCL/bf16 log warnings) | [BUG-2026-05-20-vllm-shutdown-warnings.md](bug-reports/BUG-2026-05-20-vllm-shutdown-warnings.md) | — | — | Modal vecinita-llm | L1–L3 pass |
| 2 | 2026-05-21 | Code bug | stream_tokens called self.complete() → TypeError on /generate/stream | [BUG-2026-05-21-stream-tokens-function-not-callable.md](bug-reports/BUG-2026-05-21-stream-tokens-function-not-callable.md) | — | — | Modal vecinita-llm | L1–L3 pass |
| 3 | 2026-05-21 | Code bug | Repetitive generic assistant answer + junk sources on staging chat | [BUG-2026-05-21-repetitive-assistant-answer.md](bug-reports/BUG-2026-05-21-repetitive-assistant-answer.md) | fix/repetitive-assistant-answer (local) | — | pending | L1 pass |
| 4 | 2026-05-22 | Code bug | Admin DELETE document Failed to fetch — CORS missing DELETE method | [BUG-2026-05-22-delete-document-failed-to-fetch.md](bug-reports/BUG-2026-05-22-delete-document-failed-to-fetch.md) | main | 5c81e2d | DO internal-write-api 2026-05-22 | L1–L4 pass |
