# PR remediation report — PR #68 (PRM-007)

**Session:** S001-modal-cold-start-snapshot  
**Stage:** 19-address-pr-review  
**Cycle:** PRM-007 (linked PRR-010)  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/68  
**Branch:** `fix/chat-tab-corpus-state`  
**Completed:** 2026-06-25  

## Scope

User invoked **19-address-pr-review** on PR #68 with scope **both advisories** (0 blockers, 2 🟡 from PRR-010). Session adopted into S001 routing plan (user choice).

## Findings addressed

| ID | Severity | Summary | Status | Commit |
|----|----------|---------|--------|--------|
| F-001 | advisory (concurrency defect) | `loading` not lifted with history → mid-stream Corpus switch re-enables Ask, concurrent stream possible | fixed | `d495103` |
| F-002 | advisory (cosmetic) | `useChatHistory()` fallback always runs when `chat` injected | fixed | `d495103` |

## Changes

- `useChatHistory.ts` — own `loading` + `setLoading` in the hook (lifted with messages).
- `ChatPanel.tsx` — split into `ChatPanelView` + `ChatPanelStandalone`; consume lifted loading from chat.
- `test_bug_2026_06_25_chat_mid_stream_corpus_concurrent_ask.test.tsx` — red→green regression.
- `docs/bug-reports/BUG-2026-06-25-chat-mid-stream-corpus-concurrent-ask.md` — full bug-investigation artifact.

## Verification

| Check | Result |
|-------|--------|
| Repro test | red → green |
| `npm run lint` | pass |
| `npm test` | 84 passed (17 files) |
| `npm run build` | pass |
| `ci.yml` @ `aaafe5f` | success ([run 28214739565](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/28214739565)) |

## GitHub

- F-001 inline thread replied ([comment 3478925311](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/68#discussion_r3478925311)) and **resolved**.
- Summary comment: [issue comment 4806062859](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/68#issuecomment-4806062859).

## Commits

1. `d495103` — fix(review): lift in-flight ask state + split ChatPanel (PR #68)
2. `aaafe5f` — chore(state): record PRM-007 remediation for PR #68 review
3. `878d3ae` — chore(state): close PRM-007; record CI green + GitHub resolution

**Not merged** — user merges manually.

## Follow-up

- **18-pr-review** re-run offered (user declined pending AskQuestion in close-out).
- After merge to `main`: watch `deploy-preflight.yml` per ci-after-push.
- Staging smoke H4–H5 if/when deployed (frontend behavior change).
