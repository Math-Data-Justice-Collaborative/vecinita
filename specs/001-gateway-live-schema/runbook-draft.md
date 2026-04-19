# SC-004 draft — Gateway live sign-off (operator)

1. Confirm **Render** `vecinita-gateway` has valid **`DATABASE_URL`** (internal URL from `fromDatabase` is expected).
2. If using split control plane: set **`MODAL_SCRAPER_PERSIST_VIA_GATEWAY=1`** on the gateway env group **and** on Modal **`vecinita-scraper-env`**; redeploy gateway and Modal scraper app.
3. Set **`MODAL_FUNCTION_INVOCATION=auto`** (or `1`) with **`MODAL_TOKEN_ID`** / **`MODAL_TOKEN_SECRET`** when targets use `*.modal.run`.
4. Run **`make test-schemathesis-gateway`** locally (mocked upstreams) before live CLI.
5. Run **`backend/scripts/run_schemathesis_live.sh`** with **`GATEWAY_SCHEMA_URL`** pointing at staging/production; set **`SCHEMATHESIS_SOURCE_URL`**, **`SCHEMATHESIS_MODAL_SCRAPER_JOB_ID`**, and **`SCHEMATHESIS_MODAL_GATEWAY_JOB_ID`** to real rows where possible.
6. If live checks still show **`not_a_server_error`** on Modal paths with the flag **off**, verify Modal **`MODAL_DATABASE_URL`** uses the **external** Postgres hostname (escalation: worker DSN / pipeline still on Postgres).
7. If TraceCov **`responses`** is below 100%, complete OpenAPI `responses=` on the affected routes or add a signed row to **`exception-register.md`**.
8. Capture JUnit / TraceCov HTML paths under **`SCHEMATHESIS_REPORT_DIR`** for the change record.
