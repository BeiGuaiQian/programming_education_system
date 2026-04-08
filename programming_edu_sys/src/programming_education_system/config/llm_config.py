"""Centralized runtime configuration."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Project-wide configuration with environment overrides."""

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-306f7a407dee4ed6843f6af5c56dbbda")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT = int(os.getenv("TIMEOUT", "30"))

    DEFAULT_DIFFICULTY = os.getenv("DEFAULT_DIFFICULTY", "beginner")
    KNOWLEDGE_TOPICS = [
        "python_basics",
        "data_structures",
        "algorithms",
        "oop",
        "web_development",
    ]

    LLM_CACHE_TTL = int(os.getenv("LLM_CACHE_TTL", "300"))
    MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", os.getenv("CACHE_SIZE", "1000")))
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))

    MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "5000"))
    USER_ID_PATTERN = os.getenv("USER_ID_PATTERN", r"^[a-zA-Z0-9_-]{3,50}$")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "./logs/system.log")

    _RUNTIME_DIR = Path(tempfile.gettempdir()) / "programming_education_system"
    SQLITE_CONTEXT_DB = os.getenv(
        "SQLITE_CONTEXT_DB",
        str(_RUNTIME_DIR / "learning_context.db"),
    )
    QUESTION_BANK_DB = os.getenv(
        "QUESTION_BANK_DB",
        str(_RUNTIME_DIR / "question_bank.db"),
    )

    @classmethod
    def validate_config(cls) -> bool:
        """Return whether the LLM configuration is usable."""
        if not cls.DEEPSEEK_API_KEY:
            logger.info("DEEPSEEK_API_KEY is not set; LLM features will degrade gracefully.")
            return False
        return True

    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Return normalized LLM configuration."""
        return {
            "api_key": cls.DEEPSEEK_API_KEY,
            "base_url": cls.DEEPSEEK_BASE_URL,
            "model": cls.DEEPSEEK_MODEL,
            "temperature": 0.1,
            "max_tokens": 2000,
            "timeout": cls.TIMEOUT,
            "max_retries": cls.MAX_RETRIES,
        }

    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Return Redis configuration used by context backends."""
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD", None),
            "use_redis": os.getenv("USE_REDIS", "true").lower() == "true",
        }
