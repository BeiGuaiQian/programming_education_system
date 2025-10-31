# programming_education_system/utils/llm_utils.py
"""
LLM工具函数 - 修复版
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端封装类"""

    def __init__(self):
        try:
            # 尝试导入OpenAI客户端
            from openai import AsyncOpenAI
            from programming_education_system.config.llm_config import Config

            self.client = AsyncOpenAI(
                api_key=Config.DEEPSEEK_API_KEY,
                base_url=Config.DEEPSEEK_BASE_URL
            )
            self.model = Config.DEEPSEEK_MODEL
            self.initialized = True
        except ImportError as e:
            logger.warning(f"OpenAI客户端导入失败: {e}")
            self.initialized = False
        except Exception as e:
            logger.error(f"LLM客户端初始化失败: {e}")
            self.initialized = False

        self.cache = {}  # 简单的内存缓存

    async def generate_response(self, system_prompt: str, user_message: str,
                                use_cache: bool = True) -> str:
        """
        生成LLM响应

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            use_cache: 是否使用缓存

        Returns:
            LLM响应文本
        """
        if not self.initialized:
            logger.error("LLM客户端未初始化")
            return '{"error": "LLM client not initialized"}'

        cache_key = f"{system_prompt}:{user_message}"

        # 检查缓存
        if use_cache and cache_key in self.cache:
            logger.info("Using cached response")
            return self.cache[cache_key]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content

            # 更新缓存
            if use_cache:
                self.cache[cache_key] = result
                # 简单的缓存大小控制
                if len(self.cache) > 100:
                    self.cache.pop(next(iter(self.cache)))

            return result

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return f'{{"error": "LLM request failed: {str(e)}"}}'

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# 全局LLM客户端实例
llm_client = LLMClient()