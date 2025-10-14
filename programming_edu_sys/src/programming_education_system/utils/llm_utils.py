# programming_education_system/utils/llm_utils.py
"""
LLM工具函数
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from .config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM客户端封装类"""
    
    def __init__(self):
        self.llm = ChatOpenAI(**Config.get_llm_config())
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
        cache_key = f"{system_prompt}:{user_message}"
        
        # 检查缓存
        if use_cache and cache_key in self.cache:
            logger.info("Using cached response")
            return self.cache[cache_key]
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            # 异步调用LLM
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text
            
            # 更新缓存
            if use_cache:
                self.cache[cache_key] = result
                # 简单的缓存大小控制
                if len(self.cache) > Config.CACHE_SIZE:
                    self.cache.pop(next(iter(self.cache)))
            
            return result
            
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return f"抱歉，处理请求时出现错误: {str(e)}"
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()

# 全局LLM客户端实例
llm_client = LLMClient()