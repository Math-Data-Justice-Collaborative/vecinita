# Quickstart: Validate Modal Startup Lifecycle and Connection Reliability

## 1) Set up service workspace

```bash
cd services/model-modal
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## 2) Run baseline quality checks

```bash
make lint
make test
```

## 3) Validate startup pre-pull behavior

```bash
# Pull configured default model into Modal volume
PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_default_model

# Pull a specific model id
PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_model --model-name llama3.2
```

Expected result:
- startup path reports model available before readiness.
- warm starts skip redundant full pull when model exists.

## 4) Validate lifecycle connection behavior locally

```bash
make docker-up
make docker-pull-model
curl -sS http://localhost:${API_PORT:-8000}/health
make docker-down
```

Expected result:
- health endpoint returns `status=ok`.
- model list includes preloaded model when available.

## 5) Validate required tests for connection paths

Run targeted suites while iterating:

```bash
pytest tests/test_app_runtime.py -q
pytest tests/test_models_runtime.py -q
pytest tests/test_container_setup.py -q
pytest tests/test_routes.py -q
```

Expected result:
- Unit tests cover retry, plugin validation, and teardown behavior.
- Integration-level tests cover cold/warm startup and connection failure handling.

## 6) Full CI gate from repository root

```bash
cd /root/GitHub/VECINA/vecinita
make ci
```

Expected result:
- all checks pass before implementation work is declared ready.

## 7) Operator runbook verification

Use this sequence when diagnosing startup preload failures:

```bash
cd services/model-modal
pytest tests/test_app_runtime.py -q
pytest tests/test_models_runtime.py -q
pytest tests/test_container_setup.py -q
```

Expected operator evidence:
- startup failure payload includes `error_code`, `failure_phase`, `attempt_count`,
  and `recommended_operator_action`
- lifecycle events include `correlation_id` and `retry_window_ms` where applicable
- fallback behavior is deterministic when `STARTUP_MODEL` is omitted

## 8) CI evidence capture (2026-04-20)

- `services/model-modal`: `make lint` and `pytest -q` pass.
- Repository root: `make ci` passes.
