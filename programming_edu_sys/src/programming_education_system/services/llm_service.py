from typing import Dict, Optional
from langchain.llms.base import BaseLLM
from langchain.schema import BaseMessage
import os

class LLMService:
    """LLM服务统一管理"""
    
    def __init__(self):
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """初始化LLM"""
        # 这里可以根据配置选择不同的LLM
        try:
            # 尝试使用DeepSeek
            from langchain_community.llms import DeepSeek
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key:
                self.llm = DeepSeek(api_key=api_key)
            else:
                self._setup_fallback_llm()
        except ImportError:
            self._setup_fallback_llm()
    
    def _setup_fallback_llm(self):
        """设置备用LLM"""
        from langchain.llms.fake import FakeListLLM
        self.llm = FakeListLLM(responses=["这是模拟响应"])
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """生成响应"""
        if context:
            full_prompt = f"上下文: {context}\n问题: {prompt}"
        else:
            full_prompt = prompt
        
        return self.llm.invoke(full_prompt)