# UI Tests — Reference

## Helper modules

### `mock-chat-api.ts`

| Export | Purpose |
|--------|---------|
| `mockChatApi(page, { tags? })` | `/api/v1/tags`, `/warm`, `/documents` |
| `mockChatStream(page, sseBody?)` | `/api/v1/ask/stream` SSE |
| `mockChatShell(page)` | `mockChatApi` + default stream |

Documents API mock shape:

```json
{ "items": [], "page": 1, "page_size": 20, "total": 0 }
```

Default SSE ends with `{"done":true}` — match assertions to token text in mock body.

### `mock-admin-auth.ts`

| Export | Purpose |
|--------|---------|
| `seedAdminSession(page)` | `localStorage` key `sb-placeholder-auth-token` + admin role |
| `seedViewerSession(page)` | Same storage key, viewer role |

Requires build with `VITE_SUPABASE_URL=https://placeholder.supabase.co` (see `build_for_playwright.sh`).

### `mock-admin-api.ts`

| Export | Purpose |
|--------|---------|
| `mockAdminApi(page)` | `/internal/v1/**` and `/jobs**` stubs |
| `mockAuthenticatedAdmin(page)` | auth seed + API mocks |
| `mockAuthenticatedViewer(page)` | viewer seed + API mocks |

Covers eval runs, criteria, timeseries, stats, documents, job create/poll.

### `mock-supabase-auth.ts`

| Export | Purpose |
|--------|---------|
| `mockSupabaseAuth(page)` | Unauthenticated — login page specs |

## Common `data-testid` map

### Chat (`apps/chat-rag-frontend`)

| testid | Component |
|--------|-----------|
| `sidebar` | Sidebar |
| `app-header` | App top bar |
| `language-toggle` | EN/ES buttons inside |
| `message-list` / `message` | ChatPanel |
| `tag-filter-chips` | Sidebar topic filters |
| `corpus-list` | CorpusBrowse (may be empty/hidden) |
| `previous-chats` / `previous-chats-list` | PreviousChatsList |

### Admin (`apps/data-management-frontend`)

| testid | Component |
|--------|-----------|
| `admin-nav` | AdminLayout sidebar |
| `login-form` | LoginPage |
| `viewer-read-only-notice` | JobForm (viewer) |
| `job-status` | JobForm after submit |
| `evaluation-page` | EvaluationPage |
| `evaluation-tabs` | Tab list |
| `eval-tab-*` | Individual tabs |
| `evaluation-dashboard-tab` | Dashboard panel |
| `evaluation-explore-tab` | Explore pivot |
| `evaluation-criteria-tab` | Criteria CRUD |
| `eval-pivot-row-axis` | Explore axis select |

## Example specs (copy patterns)

**Cross-navigation state (chat):** `tests/ui/chat/uj024-chat-corpus-state.spec.ts`

**Stream + message list:** `tests/ui/chat/uj001-ask-interaction.spec.ts`

**Sidebar tag → request payload:** `tests/ui/chat/uj012-tag-filter-ask.spec.ts`

**Admin nav → outlet:** `tests/ui/admin/uj020-admin-navigation.spec.ts`

**Tabs ↔ URL ↔ panel:** `tests/ui/admin/uj041-eval-dashboard-tabs.spec.ts`

**Auth roles:** `tests/ui/admin/uj029-viewer-blocked.spec.ts`

## Intercepting request bodies

```typescript
let captured: { tags?: string[] } | undefined;
await page.route("**/api/v1/ask/stream", async (route) => {
  captured = route.request().postDataJSON() as { tags?: string[] };
  await route.fulfill({ status: 200, contentType: "text/event-stream", body: sse });
});
// ... user actions ...
expect(captured?.tags).toEqual(["legal-aid"]);
```

## localStorage in browser tests

```typescript
await page.addInitScript(() => {
  localStorage.clear();
  localStorage.setItem("vecinita.locale", "en");
});
```

Read persisted UI state:

```typescript
const stored = await page.evaluate(() =>
  localStorage.getItem("vecinita.eval.explore.v1"),
);
expect(stored).toContain("case_id");
```

## CI and commands

| Command | Scope |
|---------|-------|
| `make test-ui` | build + full `tests/ui/` |
| `bash scripts/ui/run_playwright.sh` | same (npm ci + chromium install) |
| `npx playwright test --project=chat-rag` | chat specs only |
| `npx playwright test --project=data-management` | admin specs only |
| `npm run test:ui:staging` | staging project only |

GitHub Actions job: `ui-e2e` in `.github/workflows/ci.yml`.

## Finding Vitest parity

```bash
# Admin feature tests
ls apps/data-management-frontend/src/test/

# Chat feature tests  
ls apps/chat-rag-frontend/src/test/ apps/chat-rag-frontend/src/**/*.test.ts
```

Look for `test_bug_*` and `renderAppRoutesReady` — strong Playwright port candidates.

## T3-ui staging

`tests/ui/staging/staging-smoke.spec.ts` uses:

- `VECINITA_STAGING_CHAT_FRONTEND_URL`
- `VECINITA_STAGING_ADMIN_FRONTEND_URL`

No route mocks. Skip-safe via `test.skip(!envVar)`. Use for deploy smoke, not default feature work.
