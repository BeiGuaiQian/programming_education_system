"""Redis-backed context manager with graceful fallback when Redis is unavailable."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from programming_education_system.config.redis_config import CONTEXT_CONFIG, REDIS_CONFIG

logger = logging.getLogger(__name__)

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - environment dependent
    redis = None


class RedisContextManager:
    """Context manager that stores data in Redis when available."""

    def __init__(
        self,
        host: str = REDIS_CONFIG["host"],
        port: int = REDIS_CONFIG["port"],
        db: int = REDIS_CONFIG["db"],
        password: Optional[str] = REDIS_CONFIG["password"],
    ) -> None:
        self.context_ttl = CONTEXT_CONFIG["context_ttl"]
        self.learning_progress_ttl = CONTEXT_CONFIG["learning_progress_ttl"]
        self.max_history_length = CONTEXT_CONFIG["max_history_length"]
        self.available = False
        self.redis_client = None

        if redis is None:
            logger.info("Redis package is not installed; Redis context backend is disabled.")
            return

        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_keepalive=True,
            )
            self.redis_client.ping()
            self.available = True
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.info("Redis connection unavailable; Redis context backend is disabled: %s", exc)
            self.redis_client = None

    def save_conversation_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        if not self.available or self.redis_client is None:
            return False
        try:
            key = f"conversation:{user_id}"
            current = self.get_conversation_context(user_id) or {}
            merged = {**current, **context}
            self.redis_client.setex(key, self.context_ttl, self._serialize(merged))
            return True
        except Exception as exc:
            logger.error("Failed to save conversation context: %s", exc)
            return False

    def get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.available or self.redis_client is None:
            return None
        try:
            value = self.redis_client.get(f"conversation:{user_id}")
            return self._deserialize(value) if value else None
        except Exception as exc:
            logger.error("Failed to get conversation context: %s", exc)
            return None

    def save_dialog_history(self, user_id: str, dialog: Dict[str, Any]) -> bool:
        if not self.available or self.redis_client is None:
            return False
        try:
            key = f"dialog_history:{user_id}"
            self.redis_client.lpush(key, self._serialize(dialog))
            self.redis_client.ltrim(key, 0, self.max_history_length - 1)
            self.redis_client.expire(key, self.context_ttl)
            return True
        except Exception as exc:
            logger.error("Failed to save dialog history: %s", exc)
            return False

    def get_dialog_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.available or self.redis_client is None:
            return []
        try:
            key = f"dialog_history:{user_id}"
            values = self.redis_client.lrange(key, 0, max(0, limit - 1))
            history = [item for item in (self._deserialize(value) for value in values) if item]
            history.reverse()
            return history
        except Exception as exc:
            logger.error("Failed to get dialog history: %s", exc)
            return []

    def save_learning_progress(self, user_id: str, progress: Dict[str, Any]) -> bool:
        if not self.available or self.redis_client is None:
            return False
        try:
            key = f"learning_progress:{user_id}"
            current = self.get_learning_progress(user_id) or {}
            merged = {**current, **progress}
            self.redis_client.setex(key, self.learning_progress_ttl, self._serialize(merged))
            return True
        except Exception as exc:
            logger.error("Failed to save learning progress: %s", exc)
            return False

    def get_learning_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.available or self.redis_client is None:
            return None
        try:
            value = self.redis_client.get(f"learning_progress:{user_id}")
            return self._deserialize(value) if value else None
        except Exception as exc:
            logger.error("Failed to get learning progress: %s", exc)
            return None

    def clear_user_data(self, user_id: str) -> bool:
        if not self.available or self.redis_client is None:
            return False
        try:
            self.redis_client.delete(
                f"conversation:{user_id}",
                f"dialog_history:{user_id}",
                f"learning_progress:{user_id}",
            )
            return True
        except Exception as exc:
            logger.error("Failed to clear user data: %s", exc)
            return False

    def _serialize(self, data: Dict[str, Any]) -> str:
        import json

        return json.dumps(data, ensure_ascii=False, default=str)

    def _deserialize(self, data: str) -> Optional[Dict[str, Any]]:
        import json

        try:
            value = json.loads(data)
            return value if isinstance(value, dict) else None
        except Exception:
            return None
