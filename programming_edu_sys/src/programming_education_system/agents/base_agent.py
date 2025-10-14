# programming_education_system/agents/base_agent.py
"""
智能体基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求的抽象方法"""
        pass
    
    def log_activity(self, activity: str, details: Dict[str, Any] = None):
        """记录智能体活动"""
        log_message = f"{self.name}: {activity}"
        if details:
            log_message += f" - {details}"
        self.logger.info(log_message)