# programming_education_system/agents/main_agent.py
"""
主代理 - 中央调度器
"""
from typing import Dict, Any
from programming_education_system.agents.base_agent import BaseAgent

class MainAgent(BaseAgent):
    """主代理，负责意图分析和请求分发"""
    
    def __init__(self, qa_agent, exercise_agent, evaluation_agent, personal_agent):
        super().__init__("MainAgent")
        self.qa_agent = qa_agent
        self.exercise_agent = exercise_agent
        self.evaluation_agent = evaluation_agent
        self.personal_agent = personal_agent
    
    async def receive_from_user_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """接收用户代理请求"""
        self.log_activity("接收用户代理请求", {"request_type": request["type"]})
        return await self.process(request)
    
    async def analyze_intent(self, request: Dict[str, Any]) -> str:
        """分析用户意图"""
        content = request["content"].lower()
        request_type = request["type"]
        
        # 如果已经指定了类型，直接使用
        if request_type in ["qa", "exercise", "evaluation", "personal"]:
            return request_type
        
        # 基于内容分析意图
        if any(word in content for word in ["怎么", "如何", "为什么", "什么是", "解释"]):
            return "qa"
        elif any(word in content for word in ["练习", "题目", "测试", "作业"]):
            return "exercise"
        elif any(word in content for word in ["评价", "评分", "检查代码"]):
            return "evaluation"
        elif any(word in content for word in ["建议", "路径", "学习计划"]):
            return "personal"
        else:
            return "qa"  # 默认答疑
    
    async def dispatch_to_sub_agent(self, intent: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """分发请求到子代理"""
        self.log_activity("分发请求到子代理", {"intent": intent})
        
        agents = {
            "qa": self.qa_agent,
            "exercise": self.exercise_agent,
            "evaluation": self.evaluation_agent,
            "personal": self.personal_agent
        }
        
        target_agent = agents.get(intent, self.qa_agent)
        return await target_agent.process(request)
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        # 分析意图
        intent = await self.analyze_intent(request)
        self.log_activity("意图分析完成", {"intent": intent})
        
        # 分发到对应代理
        result = await self.dispatch_to_sub_agent(intent, request)
        
        # 记录用户行为（简化）
        behavior_data = {
            "user_id": request["user_id"],
            "intent": intent,
            "content": request["content"],
            "timestamp": request["timestamp"]
        }
        await self.personal_agent.track_user_behavior(behavior_data)
        
        return result