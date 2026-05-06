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

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", DEEPSEEK_API_KEY).strip()
    EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", DEEPSEEK_BASE_URL)
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    RAG_USE_VECTOR = os.getenv("RAG_USE_VECTOR", "false").lower() == "true"
    RAG_VECTOR_DB = os.getenv(
        "RAG_VECTOR_DB",
        str(Path(tempfile.gettempdir()) / "programming_education_system" / "rag_vectors.db"),
    )
    RAG_VECTOR_WEIGHT = float(os.getenv("RAG_VECTOR_WEIGHT", "0.65"))
    RAG_LEXICAL_WEIGHT = float(os.getenv("RAG_LEXICAL_WEIGHT", "0.35"))
    RAG_RETRIEVAL_LIMIT = int(os.getenv("RAG_RETRIEVAL_LIMIT", "4"))

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
    MAX_CODE_LENGTH = int(os.getenv("MAX_CODE_LENGTH", "12000"))
    ENABLE_UNTRUSTED_CODE_EXECUTION = (
        os.getenv("ENABLE_UNTRUSTED_CODE_EXECUTION", "false").lower() == "true"
    )
    CODE_EXECUTION_TIMEOUT = int(os.getenv("CODE_EXECUTION_TIMEOUT", "5"))

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
        if not cls.has_valid_api_key():
            logger.info("DEEPSEEK_API_KEY is not set; LLM features will degrade gracefully.")
            return False
        return True

    @classmethod
    def has_valid_api_key(cls) -> bool:
        """Return whether the configured API key looks usable."""
        key = cls.DEEPSEEK_API_KEY.strip()
        if not key:
            return False

        placeholder_markers = (
            "your_",
            "replace_",
            "example",
            "placeholder",
            "test_key",
        )
        lowered = key.lower()
        return not any(marker in lowered for marker in placeholder_markers)

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
    def has_valid_embedding_key(cls) -> bool:
        key = cls.EMBEDDING_API_KEY.strip()
        if not key:
            return False
        lowered = key.lower()
        return not any(
            marker in lowered
            for marker in ("your_", "replace_", "example", "placeholder", "test_key")
        )

    @classmethod
    def get_embedding_config(cls) -> Dict[str, Any]:
        """Return normalized embedding configuration."""
        return {
            "api_key": cls.EMBEDDING_API_KEY,
            "base_url": cls.EMBEDDING_BASE_URL,
            "model": cls.EMBEDDING_MODEL,
            "timeout": cls.TIMEOUT,
            "enabled": cls.RAG_USE_VECTOR and cls.has_valid_embedding_key(),
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
