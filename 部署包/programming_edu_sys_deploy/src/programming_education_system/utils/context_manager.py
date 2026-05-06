"""Select the most appropriate context storage backend."""

from __future__ import annotations

import logging

from dotenv import load_dotenv

from programming_education_system.config.llm_config import Config

load_dotenv()

logger = logging.getLogger(__name__)


def get_context_manager():
    """Create a context backend with Redis -> SQLite -> memory fallback."""
    redis_config = Config.get_redis_config()

    if redis_config["use_redis"]:
        try:
            from .redis_context import RedisContextManager

            manager = RedisContextManager(
                host=redis_config["host"],
                port=redis_config["port"],
                db=redis_config["db"],
                password=redis_config["password"],
            )
            if getattr(manager, "available", False):
                logger.info("Using Redis context manager.")
                return manager
            logger.info("Redis backend is unavailable; falling back to SQLite.")
        except Exception as exc:
            logger.info("Redis unavailable, falling back to SQLite: %s", exc)

    try:
        from .sqlite_context import SQLiteContextManager

        logger.info("Using SQLite context manager.")
        return SQLiteContextManager()
    except Exception as exc:
        logger.info("SQLite unavailable, falling back to in-memory context: %s", exc)
        from .memory_context import MemoryContextManager

        logger.info("Using in-memory context manager.")
        return MemoryContextManager()


context_manager = get_context_manager()
