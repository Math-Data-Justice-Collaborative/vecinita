# shared-logging

Shared structured JSON logging setup for all Vecinita backend services.

## Usage

```bash
pip install -e ../../packages/shared-logging
```

```python
from shared_logging import get_logger

logger = get_logger(__name__)
logger.info("Service started", extra={"port": 8000})
```

## Design Rules

- This package **must not** import from any `apps/` service
- Only `python-json-logger` is allowed as a runtime dependency
