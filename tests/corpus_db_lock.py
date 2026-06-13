"""Serialize mutations to the shared Postgres corpus across parallel test setup."""

from __future__ import annotations

import threading

corpus_db_lock = threading.RLock()
