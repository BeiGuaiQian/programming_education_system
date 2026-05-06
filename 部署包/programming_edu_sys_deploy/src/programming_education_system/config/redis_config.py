"""Redis and context storage configuration."""

from __future__ import annotations

import os
from typing import Any, Dict

REDIS_CONFIG: Dict[str, Any] = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD") or None,
    "decode_responses": True,
}

CONTEXT_CONFIG: Dict[str, Any] = {
    "max_history_length": int(os.getenv("MAX_HISTORY_LENGTH", 50)),
    "context_ttl": int(os.getenv("CONTEXT_TTL", 7 * 24 * 3600)),
    "learning_progress_ttl": int(os.getenv("LEARNING_PROGRESS_TTL", 30 * 24 * 3600)),
}
