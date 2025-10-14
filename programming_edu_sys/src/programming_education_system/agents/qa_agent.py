# programming_education_system/agents/qa_agent.py
"""
答疑代理
"""
from typing import Dict, Any
import re
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.models.knowledge_base import KnowledgeBase
from programming_education_system.agents.base_agent import BaseAgent

class ThinkingQAAgent:
    """思考答疑子代理"""
    
    def __init__(self):
        self.name = "ThinkingQAAgent"
    
    async def think_and_answer(self, complex_question: str, context: Dict[str, Any] = None) -> str:
        """处理复杂问题分析"""
        system_prompt = """你是一个编程教育专家，擅长用清晰易懂的方式解释复杂的编程概念。
请用结构化、示例丰富的方式回答编程问题，确保学习者能够理解。"""
        
        user_message = f"问题：{complex_question}\n\n请详细解释这个问题："
        
        if context:
            user_message += f"\n上下文信息：{context}"
        
        return await llm_client.generate_response(system_prompt, user_message)

class KnowledgeBaseRetrievalAgent:
    """知识库检索子代理"""
    
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
    
    async def retrieve_from_knowledge_base(self, question: str) -> Dict[str, Any]:
        """从知识库检索答案"""
        results = self.knowledge_base.search(question)
        
        if results:
            # 返回最相关的结果
            best_match = results[0]
            return {
                "found": True,
                "answer": best_match["answer"],
                "examples": best_match.get("examples", []),
                "source": "knowledge_base"
            }
        else:
            return {"found": False, "answer": "知识库中未找到相关问题"}

class QAAgent(BaseAgent):
    """答疑代理"""
    
    def __init__(self, personal_agent):
        super().__init__("QAAgent")
        self.thinking_agent = ThinkingQAAgent()
        self.kb_agent = KnowledgeBaseRetrievalAgent()
        self.personal_agent = personal_agent
    
    async def answer_question(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """回答问题总入口"""
        self.log_activity("开始处理问题", {"question": question[:50] + "..."})
        
        # 首先尝试知识库检索
        kb_result = await self.kb_agent.retrieve_from_knowledge_base(question)
        
        if kb_result["found"]:
            self.log_activity("从知识库找到答案")
            return {
                "response": kb_result["answer"],
                "examples": kb_result.get("examples", []),
                "source": "knowledge_base",
                "needs_thinking": False
            }
        else:
            # 复杂问题需要思考分析
            self.log_activity("使用思考代理处理复杂问题")
            thinking_answer = await self.thinking_agent.think_and_answer(question, context)
            
            return {
                "response": thinking_answer,
                "examples": [],
                "source": "llm_thinking",
                "needs_thinking": True
            }
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理答疑请求"""
        question = request["content"]
        user_id = request["user_id"]
        
        # 回答问题
        result = await self.answer_question(question)
        
        # 更新用户画像（记录提问行为）
        behavior_data = {
            "user_id": user_id,
            "question_type": "qa",
            "topic": self._extract_topic(question),
            "complexity": "complex" if result["needs_thinking"] else "simple"
        }
        await self.personal_agent.track_user_behavior(behavior_data)
        
        return {
            "response": result["response"],
            "details": {
                "source": result["source"],
                "examples": result["examples"]
            }
        }
    
    def _extract_topic(self, question: str) -> str:
        """从问题中提取主题"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["函数", "def", "参数"]):
            return "python_basics"
        elif any(word in question_lower for word in ["列表", "字典", "元组", "集合"]):
            return "data_structures"
        elif any(word in question_lower for word in ["算法", "排序", "查找", "递归"]):
            return "algorithms"
        elif any(word in question_lower for word in ["类", "对象", "继承", "多态"]):
            return "oop"
        else:
            return "python_basics"