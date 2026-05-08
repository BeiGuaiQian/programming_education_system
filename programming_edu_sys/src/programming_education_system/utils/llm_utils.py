"""Shared LLM utilities with graceful fallback behavior."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

from programming_education_system.config.llm_config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """Async LLM client wrapper with retry, caching, and offline fallback."""

    def __init__(self) -> None:
        self.cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self.cache_ttl = Config.LLM_CACHE_TTL
        self.max_cache_size = Config.MAX_CACHE_SIZE
        self.max_retries = Config.MAX_RETRIES
        self.timeout = Config.TIMEOUT
        self.initialized = False
        self.client = None
        self.model = Config.DEEPSEEK_MODEL
        self.openai_error_types = (Exception,)
        self.fallback_reason = "uninitialized"
        self.failure_count = 0
        self.circuit_open_until = 0.0
        self.circuit_breaker_threshold = 3
        self.circuit_breaker_seconds = 45
        self._initialize_client()

    def _initialize_client(self) -> None:
        try:
            from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError

            if not Config.has_valid_api_key():
                self.fallback_reason = "missing_api_key"
                logger.info("LLM API key is not configured; using fallback responses.")
                return

            self.client = AsyncOpenAI(
                api_key=Config.DEEPSEEK_API_KEY,
                base_url=Config.DEEPSEEK_BASE_URL,
                timeout=self.timeout,
                max_retries=0,
            )
            self.openai_error_types = (APIError, APITimeoutError, RateLimitError)
            self.initialized = True
            self.fallback_reason = ""
            logger.info("LLM client initialized with model %s", self.model)
        except ImportError as exc:
            self.fallback_reason = "missing_openai_sdk"
            logger.info("OpenAI SDK is not installed; using fallback responses.")
        except Exception as exc:
            self.fallback_reason = "initialization_failed"
            logger.info("LLM client initialization failed; using fallback responses: %s", exc)

    def _generate_cache_key(self, system_prompt: str, user_message: str) -> str:
        content = f"{system_prompt}\n---\n{user_message}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        cached_item = self.cache.get(cache_key)
        if not cached_item:
            return None
        if time.time() - cached_item["timestamp"] >= self.cache_ttl:
            self.cache.pop(cache_key, None)
            return None
        self.cache.move_to_end(cache_key)
        return str(cached_item["response"])

    def _set_cached_response(self, cache_key: str, response: str) -> None:
        if len(self.cache) >= self.max_cache_size:
            self.cache.popitem(last=False)
        self.cache[cache_key] = {"response": response, "timestamp": time.time()}

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        use_cache: bool = True,
        task_type: str = "general",
    ) -> str:
        return await self.generate_response_with_retry(
            system_prompt=system_prompt,
            user_message=user_message,
            use_cache=use_cache,
            max_retries=self.max_retries,
            task_type=task_type,
        )

    async def generate_response_with_retry(
        self,
        system_prompt: str,
        user_message: str,
        use_cache: bool = True,
        max_retries: int = 3,
        task_type: str = "general",
    ) -> str:
        cache_key = self._generate_cache_key(system_prompt, user_message) if use_cache else None
        if cache_key:
            cached = self._get_cached_response(cache_key)
            if cached is not None:
                return cached

        if not self.initialized or self.client is None:
            response = self._get_fallback_response(
                system_prompt,
                user_message,
                self.fallback_reason or "llm_unavailable",
                task_type=task_type,
            )
            if cache_key:
                self._set_cached_response(cache_key, response)
            return response

        if time.time() < self.circuit_open_until:
            response = self._get_fallback_response(
                system_prompt,
                user_message,
                "llm_circuit_open",
                task_type=task_type,
            )
            if cache_key:
                self._set_cached_response(cache_key, response)
            return response

        last_exception: Optional[Exception] = None
        for attempt in range(max(1, max_retries)):
            try:
                result = await self._request_completion(system_prompt, user_message)
                self.failure_count = 0
                self.circuit_open_until = 0.0
                if cache_key:
                    self._set_cached_response(cache_key, result)
                return result
            except self.openai_error_types as exc:
                last_exception = exc
                self._record_failure()
                if attempt < max(1, max_retries) - 1:
                    await asyncio.sleep(self._calculate_backoff(attempt))
            except Exception as exc:
                last_exception = exc
                self._record_failure()
                break

        response = self._get_fallback_response(
            system_prompt,
            user_message,
            str(last_exception) if last_exception else "unknown_error",
            task_type=task_type,
        )
        if cache_key:
            self._set_cached_response(cache_key, response)
        return response

    async def _request_completion(self, system_prompt: str, user_message: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        return content if isinstance(content, str) else str(content)

    def _calculate_backoff(self, attempt: int) -> float:
        return min(3.0, (2**attempt) + random.uniform(0, 0.3))

    def _record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.circuit_breaker_threshold:
            self.circuit_open_until = time.time() + self.circuit_breaker_seconds
            logger.warning(
                "LLM circuit breaker opened for %s seconds after %s failures.",
                self.circuit_breaker_seconds,
                self.failure_count,
            )

    def _get_fallback_response(
        self,
        system_prompt: str,
        user_message: str,
        error_msg: str,
        task_type: str = "general",
    ) -> str:
        logger.info("Using fallback LLM response due to: %s", error_msg)

        task_type = (task_type or "general").lower()
        if task_type in {"router", "intent"}:
            return (
                '{"intent":"qa","topic":"general_programming","difficulty":"beginner",'
                '"confidence":0.2,"reason":"llm_unavailable","needs_code_review":false,'
                '"needs_exercise_context":false,"teaching_mode":"explain"}'
            )
        if task_type in {"user_context", "context"}:
            return (
                '{"action":"plain","intent":"qa","optimized_input":"","topic_hint":"general_programming",'
                '"user_requirement":"","context_summary":"","already_answered":[],"avoid_repeating":[],'
                '"relevant_turns":[],"use_last_question":false,"needs_exercise_context":false,'
                '"confidence":0.2,"reason":"llm_unavailable"}'
            )
        if task_type == "evaluation":
            return "目前无法调用大模型，我先给出基于规则的代码分析结果。"
        if task_type == "exercise":
            return "目前无法调用大模型，我先按基础模式为你处理练习相关请求。"
        if task_type == "personal":
            return "目前无法调用大模型，我先根据现有学习记录给出基础建议。"
        if task_type == "qa":
            return "目前无法调用大模型，我先根据课程资料和当前问题给出简要解释。"
        return "目前无法调用大模型，我先按系统内置逻辑继续处理。"

    def clear_cache(self) -> None:
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self.cache),
            "max_size": self.max_cache_size,
            "ttl": self.cache_ttl,
            "initialized": self.initialized,
            "model": self.model,
            "failure_count": self.failure_count,
            "circuit_open": time.time() < self.circuit_open_until,
        }

    def set_cache_ttl(self, ttl: int) -> None:
        self.cache_ttl = max(1, int(ttl))


llm_client = LLMClient()
