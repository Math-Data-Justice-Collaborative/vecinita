# Gateway live operations (Schemathesis / Modal jobs)

Short operator checklist for gateway contract checks and Modal scraper reliability (SC-004).

1. Verify **`DATABASE_URL`** on **`vecinita-gateway`** (Render `fromDatabase` internal URL is valid for gateway-owned persistence).
2. For Modal-native scraper control plane without Modal Postgres on **submit**: set **`MODAL_SCRAPER_PERSIST_VIA_GATEWAY=1`** on the gateway and on Modal **`vecinita-scraper-env`**, then redeploy both.
3. Ensure **`MODAL_FUNCTION_INVOCATION`** and Modal tokens are set when using **`Function.from_name`** (`backend/src/services/modal/invoker.py`).
4. Run **`make test-schemathesis-gateway`** before shipping OpenAPI or router changes.
5. For live smoke: **`backend/scripts/run_schemathesis_live.sh`** with **`GATEWAY_SCHEMA_URL`**; tune **`SCHEMATHESIS_SOURCE_URL`**, **`SCHEMATHESIS_MODAL_SCRAPER_JOB_ID`**, **`SCHEMATHESIS_MODAL_GATEWAY_JOB_ID`** to reduce 404 noise.
6. If Modal still hits Postgres for **workers**, keep **`MODAL_DATABASE_URL`** on Modal pointed at the **external** database URL until workers are migrated.
7. On TraceCov failure, fix OpenAPI **`responses=`** or record a waiver in **`specs/001-gateway-live-schema/exception-register.md`**.
8. On persistent 5xx from Modal RPC with the flag **disabled**, treat as **connectivity / DSN** escalation (see **`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`**).
