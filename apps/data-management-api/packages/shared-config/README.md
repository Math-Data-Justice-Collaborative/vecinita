# shared-config

Shared configuration utilities and base settings class for the Vecinita platform.

## Usage

```bash
pip install -e ../../packages/shared-config
```

```python
from shared_config import get_settings

settings = get_settings()
print(settings.port)
```

## Design Rules

- This package **must not** import from any `apps/` service
- Only `pydantic-settings` is allowed as a runtime dependency
- Each service extends `BaseServiceSettings` to add its own fields
