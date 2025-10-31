# programming_education_system/utils/llm_config.py
"""
系统配置文件
"""
import os
from typing import Dict, Any

class Config:
    """系统配置类"""
    
    # DeepSeek API 配置
    DEEPSEEK_API_KEY = "sk-566bbf4add084155ab4b31c17e9d71e6"
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    
    # 系统配置
    MAX_RETRIES = 3
    TIMEOUT = 30
    CACHE_SIZE = 100
    
    # 学习参数
    DEFAULT_DIFFICULTY = "beginner"
    KNOWLEDGE_TOPICS = ["python_basics", "data_structures", "algorithms", "oop", "web_development"]
    
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """获取LLM配置"""
        return {
            "api_key": cls.DEEPSEEK_API_KEY,
            "base_url": cls.DEEPSEEK_BASE_URL,
            "model": cls.DEEPSEEK_MODEL,
            "temperature": 0.1,
            "max_tokens": 2000
        }