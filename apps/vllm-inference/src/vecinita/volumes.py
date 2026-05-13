"""Modal persistent volume used to cache downloaded model weights."""

import modal

from .config import settings

# A named volume that persists model weights across container restarts.
# Mount it at MODELS_PATH inside any container that needs model access.
models_volume = modal.Volume.from_name("vecinita-models", create_if_missing=True)

MODELS_PATH = settings.models_path
