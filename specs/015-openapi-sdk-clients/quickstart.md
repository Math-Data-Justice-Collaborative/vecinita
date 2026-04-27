# Quickstart: OpenAPI clients + approved env (feature 015)

For developers validating **015-openapi-sdk-clients** locally after `tasks.md` is implemented.

## 1. Environment

Copy from **`.env.local.example`** (or team secret manager). Set **only** approved connectivity vars for cross-service work:

| Variable | Example purpose |
|----------|-----------------|
| `DATABASE_URL` | Local or Render Postgres |
| `RENDER_GATEWAY_URL` | Gateway origin |
| `RENDER_AGENT_URL` | Agent origin |
| `DATA_MANAGEMENT_API_URL` | DM API origin |
| `GATEWAY_SCHEMA_URL` | Gateway OpenAPI JSON |
| `DATA_MANAGEMENT_SCHEMA_URL` | DM OpenAPI JSON |
| `AGENT_SCHEMA_URL` | Agent OpenAPI JSON |

**Do not set** (should be absent from examples after migration):  
`MODAL_OLLAMA_ENDPOINT`, `MODAL_EMBEDDING_ENDPOINT`, `VECINITA_MODEL_API_URL`, `VECINITA_EMBEDDING_API_URL`, `EMBEDDING_SERVICE_URL`.

Modal **SDK auth** (when invoking Modal from Python): use documented **`MODAL_TOKEN_ID`** / **`MODAL_TOKEN_SECRET`** (or workspace equivalents)—not URL endpoints for model/embedding.

## 2. Regenerate clients

After [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md) lands, use repo **`Makefile`** targets (exact names in `tasks.md`), e.g.:

```bash
make openapi-codegen   # placeholder — wire in tasks
```

Expect **network** to the three schema URLs unless using an explicit offline/stash workflow (default: failures must be loud per spec edge cases).

## 3. Validate contracts

```bash
make test-schemathesis          # offline where configured
# optional live:
make test-schemathesis-cli      # uses GATEWAY_SCHEMA_URL, DATA_MANAGEMENT_SCHEMA_URL, optional AGENT_SCHEMA_URL
```

See root **`TESTING_DOCUMENTATION.md`**.

## 4. Modal HTTP ban (SC-005)

```bash
make check-modal-http   # placeholder — implement per contracts/modal-http-ban-sc005.md
```

Must exit **0** on clean tree.

## 5. Full gate

```bash
make ci
```

## 6. Docs

If **`docs-gh-pages.yml`** publishes env tables, verify it lists only **FR-004** URL variables for service connectivity and links to this feature’s contracts.

## 7. Staging release (SC-004)

After **T045** lands, operators follow **`docs/deployment/SC004_STAGING_RELEASE_CHECKLIST.md`** (linked from `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` when wired) for baseline metrics, the one-week p95 comparison, and sign-off—this is not automated in `make ci`.
