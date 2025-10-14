# programming_education_system/agents/user_agent.py
"""
用户代理
"""
from typing import Dict, Any
from programming_education_system.agents.base_agent import BaseAgent

class UserAgent(BaseAgent):
    """用户代理，负责与用户交互"""
    
    def __init__(self, main_agent):
        super().__init__("UserAgent")
        self.main_agent = main_agent
        self.current_user_id = None
    
    async def receive_user_request(self, request_type: str, content: str, user_id: str) -> Dict[str, Any]:
        """
        接收用户请求
        
        Args:
            request_type: 请求类型 (qa, exercise, evaluation, personal)
            content: 请求内容
            user_id: 用户ID
            
        Returns:
            处理结果
        """
        self.current_user_id = user_id
        self.log_activity("接收用户请求", {
            "user_id": user_id,
            "request_type": request_type,
            "content": content
        })
        
        # 构建请求对象
        request = {
            "type": request_type,
            "content": content,
            "user_id": user_id,
            "timestamp": "2024-01-01 10:00:00"  # 简化时间戳
        }
        
        # 转发给主代理
        return await self.forward_to_main_agent(request)
    
    async def forward_to_main_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """转发请求给主代理"""
        self.log_activity("转发请求给主代理", {"request_type": request["type"]})
        return await self.main_agent.process(request)
    
    async def collect_and_return_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """收集并返回结果给用户"""
        self.log_activity("返回结果给用户", {"result_type": type(results).__name__})
        
        # 格式化返回结果
        formatted_result = {
            "success": True,
            "user_id": self.current_user_id,
            "response": results.get("response", "请求处理完成"),
            "details": results.get("details", {}),
            "suggestions": results.get("suggestions", [])
        }
        
        return formatted_result
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求（BaseAgent要求实现）"""
        # UserAgent的处理逻辑在receive_user_request中实现
        return await self.receive_user_request(
            request.get("type", "qa"),
            request.get("content", ""),
            request.get("user_id", "anonymous")
        )