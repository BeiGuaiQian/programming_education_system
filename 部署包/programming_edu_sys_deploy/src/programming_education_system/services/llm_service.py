"""Compatibility wrapper around the shared LLM client."""

from __future__ import annotations

import asyncio
from typing import Dict, Optional

from programming_education_system.utils.llm_utils import llm_client


class LLMService:
    """Synchronous service facade used by legacy call sites."""

    def __init__(self):
        self.llm = llm_client

    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate a response from the shared async LLM client."""
        system_prompt = "You are a helpful programming education assistant."
        user_message = f"Context: {context}\nQuestion: {prompt}" if context else prompt

        try:
            return asyncio.run(
                self.llm.generate_response(system_prompt=system_prompt, user_message=user_message)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.llm.generate_response(
                        system_prompt=system_prompt,
                        user_message=user_message,
                    )
                )
            finally:
                loop.close()
