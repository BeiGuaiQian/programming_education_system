# src/programming_education_system/agents/qa_agent.py (改进版本)
"""
答疑代理 - 增强交互支持
"""
from typing import Dict, Any, List
import logging

# 使用相对导入
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.models.knowledge_base import KnowledgeBase
from programming_education_system.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ThinkingQAAgent:
    """思考答疑子代理 - 增强版"""

    def __init__(self):
        self.name = "ThinkingQAAgent"

    async def think_and_answer(self, complex_question: str, context: Dict[str, Any] = None) -> str:
        """处理复杂问题分析 - 增强交互性"""
        system_prompt = """你是一个耐心、专业的编程教育专家，擅长用清晰易懂的方式解释复杂的编程概念。
请用结构化、示例丰富的方式回答编程问题，确保学习者能够理解。
回答时要：
1. 先给出简要的直接答案
2. 然后详细解释概念
3. 提供实用的代码示例
4. 最后给出学习建议
请用友好的语气，避免使用过于专业的术语。"""

        user_message = f"学习者提问：{complex_question}"

        if context:
            user_message += f"\n学习上下文：{context}"

        user_message += "\n\n请用教育性的方式回答这个问题："

        return await llm_client.generate_response(system_prompt, user_message)


class KnowledgeBaseRetrievalAgent:
    """知识库检索子代理 - 增强版"""

    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        # 增强知识库内容
        self._enhance_knowledge_base()

    def _enhance_knowledge_base(self):
        """增强知识库内容"""
        enhanced_knowledge = {
            "python_basics": [
                {
                    "question": "如何开始学习Python？",
                    "answer": "学习Python的建议路径：1. 先学习基础语法 2. 练习简单的程序 3. 学习常用数据结构 4. 尝试小项目",
                    "examples": ["推荐资源：Python官方文档、Codecademy、廖雪峰的Python教程"]
                }
            ],
            "interactive_help": [
                {
                    "question": "系统能做什么？",
                    "answer": "我可以帮你：1. 回答编程问题 2. 生成练习题目 3. 评价你的代码 4. 提供个性化学习建议",
                    "examples": ["试试问我：'生成一个Python练习' 或 '评价我的代码'"]
                }
            ]
        }

        for topic, items in enhanced_knowledge.items():
            for item in items:
                self.knowledge_base.add_knowledge(
                    topic, item["question"], item["answer"], item.get("examples", [])
                )

    async def retrieve_from_knowledge_base(self, question: str) -> Dict[str, Any]:
        """从知识库检索答案 - 增强匹配"""
        results = self.knowledge_base.search(question)

        if results:
            best_match = results[0]
            return {
                "found": True,
                "answer": best_match["answer"],
                "examples": best_match.get("examples", []),
                "source": "knowledge_base",
                "confidence": "high"
            }
        else:
            return {"found": False, "answer": ""}


class QAAgent(BaseAgent):
    """答疑代理 - 增强交互支持"""

    def __init__(self, personal_agent):
        super().__init__("QAAgent")
        self.thinking_agent = ThinkingQAAgent()
        self.kb_agent = KnowledgeBaseRetrievalAgent()
        self.personal_agent = personal_agent

    async def answer_question(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """回答问题总入口 - 增强用户体验"""
        self.log_activity("开始处理问题", {"question": question})

        # 首先尝试知识库检索
        kb_result = await self.kb_agent.retrieve_from_knowledge_base(question)

        if kb_result["found"] and kb_result["confidence"] == "high":
            self.log_activity("从知识库找到高质量答案")
            return {
                "response": kb_result["answer"],
                "examples": kb_result.get("examples", []),
                "source": "knowledge_base",
                "needs_thinking": False
            }
        else:
            # 复杂问题需要思考分析
            self.log_activity("使用思考代理处理问题")
            thinking_answer = await self.thinking_agent.think_and_answer(question, context)

            return {
                "response": thinking_answer,
                "examples": [],
                "source": "llm_thinking",
                "needs_thinking": True
            }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理答疑请求 - 增强响应格式"""
        question = request["content"]
        user_id = request["user_id"]

        # 回答问题
        result = await self.answer_question(question)

        # 更新用户画像（记录提问行为）
        topic = self._extract_topic(question)
        behavior_data = {
            "user_id": user_id,
            "question_type": "qa",
            "topic": topic,
            "complexity": "complex" if result["needs_thinking"] else "simple",
            "content": question[:100]  # 记录前100个字符
        }
        await self.personal_agent.track_user_behavior(behavior_data)

        # 构建响应
        response_data = {
            "response": result["response"],
            "details": {
                "source": result["source"],
                "examples": result["examples"],
                "topic": topic,
                "answer_type": "detailed" if result["needs_thinking"] else "quick"
            }
        }

        # 添加学习建议
        if result["needs_thinking"]:
            # 对于复杂问题，添加进一步学习的建议
            learning_tips = await self._generate_learning_tips(topic)
            response_data["details"]["learning_tips"] = learning_tips

        return response_data

    def _extract_topic(self, question: str) -> str:
        """从问题中提取主题 - 增强识别"""
        question_lower = question.lower()

        topic_keywords = {
            "python_basics": ["python", "函数", "def", "参数", "变量", "语法"],
            "data_structures": ["列表", "字典", "元组", "集合", "数组", "数据结构"],
            "algorithms": ["算法", "排序", "查找", "递归", "复杂度", "二分"],
            "oop": ["类", "对象", "继承", "多态", "封装", "面向对象"],
            "web_development": ["网页", "网站", "flask", "django", "html", "css"],
            "data_science": ["数据", "分析", "pandas", "numpy", "可视化", "机器学习"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                return topic

        return "general_programming"

    async def _generate_learning_tips(self, topic: str) -> List[str]:
        """生成学习建议"""
        tips_map = {
            "python_basics": [
                "建议多练习函数定义和调用",
                "尝试编写小工具来巩固基础语法",
                "阅读Python官方文档的基础部分"
            ],
            "data_structures": [
                "动手实现各种数据结构",
                "练习在不同场景下选择合适的数据结构",
                "学习算法复杂度分析"
            ],
            "algorithms": [
                "从简单的排序算法开始学习",
                "多画图理解算法执行过程",
                "在在线判题系统上练习"
            ],
            "general_programming": [
                "坚持每天编码练习",
                "阅读优秀的开源代码",
                "参与编程社区讨论"
            ]
        }

        return tips_map.get(topic, tips_map["general_programming"])