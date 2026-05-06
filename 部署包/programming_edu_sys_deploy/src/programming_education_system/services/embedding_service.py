"""Embedding client used by the RAG vector index."""

from __future__ import annotations

import logging
from typing import List

from programming_education_system.config.llm_config import Config

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Small synchronous wrapper around an OpenAI-compatible embeddings API."""

    def __init__(self) -> None:
        self.config = Config.get_embedding_config()
        self.client = None
        self.initialized = False
        self.failure_reason = "disabled"
        self._initialize_client()

    def _initialize_client(self) -> None:
        if not self.config["enabled"]:
            self.failure_reason = "embedding_disabled_or_missing_key"
            return
        try:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=self.config["api_key"],
                base_url=self.config["base_url"],
                timeout=self.config["timeout"],
            )
            self.initialized = True
            self.failure_reason = ""
        except Exception as exc:
            self.failure_reason = f"embedding_init_failed: {exc}"
            logger.info("Embedding client unavailable: %s", exc)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts. Return an empty list when unavailable."""
        if not texts or not self.initialized or self.client is None:
            return []
        try:
            response = self.client.embeddings.create(
                model=self.config["model"],
                input=texts,
            )
            return [list(item.embedding) for item in response.data]
        except Exception as exc:
            logger.warning("Embedding request failed: %s", exc)
            return []

    def embed_query(self, text: str) -> List[float]:
        vectors = self.embed_texts([text])
        return vectors[0] if vectors else []


embedding_client = EmbeddingClient()
