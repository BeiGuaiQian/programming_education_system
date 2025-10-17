# src/programming_education_system/agents/qa_agent.py (集成认知评估版本)
"""
答疑代理 - 集成认知评估增强版
"""
from typing import Dict, Any, List
import logging
import asyncio

# 使用相对导入
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.models.knowledge_base import KnowledgeBase
from programming_education_system.agents.base_agent import BaseAgent

# 导入认知评估
from programming_education_system.cognition_judger.cognitive_api import get_cognition_api

logger = logging.getLogger(__name__)


class ThinkingQAAgent:
    """思考答疑子代理 - 集成认知评估"""

    def __init__(self):
        self.name = "ThinkingQAAgent"
        self.cognition_api = get_cognition_api()

    async def think_and_answer(self, complex_question: str, user_id: str, context: Dict[str, Any] = None) -> Dict[
        str, Any]:
        """处理复杂问题分析 - 基于认知水平个性化"""

        # 获取用户认知水平和个性化参数
        cognitive_profile = await self.cognition_api.get_cognitive_level(user_id)
        personalization_params = await self.cognition_api.get_adaptive_content_parameters(user_id)

        # 基于认知水平调整系统提示
        system_prompt = self._build_system_prompt(cognitive_profile, personalization_params)

        user_message = f"学习者提问：{complex_question}"

        if context:
            user_message += f"\n学习上下文：{context}"

        user_message += "\n\n请用适合学习者水平的方式回答这个问题："

        # 生成回答
        answer = await llm_client.generate_response(system_prompt, user_message)

        return {
            "answer": answer,
            "cognitive_level_used": cognitive_profile["overall_level"],
            "explanation_depth": personalization_params["explanation_depth"],
            "personalization_applied": True
        }

    def _build_system_prompt(self, cognitive_profile: Dict[str, Any], personalization: Dict[str, Any]) -> str:
        """基于认知水平构建系统提示"""

        cognitive_level = cognitive_profile["overall_level"]
        explanation_depth = personalization["explanation_depth"]

        base_prompt = "你是一个耐心、专业的编程教育专家，擅长根据学习者的认知水平调整解释方式。"

        if cognitive_level < 0.4:
            # 初学者级别
            return f"""{base_prompt}
你正在教一个编程初学者。请用以下方式回答：
1. 使用简单易懂的语言，避免专业术语
2. 提供具体的、一步一步的解释
3. 多用类比和生活化的例子
4. 鼓励学习者，给予正面反馈
5. 解释深度：{explanation_depth:.1f}（较浅显易懂）

请确保回答友好、支持性，帮助建立学习信心。"""

        elif cognitive_level < 0.7:
            # 中级水平
            return f"""{base_prompt}
你正在教一个有基础的学习者。请用以下方式回答：
1. 平衡概念解释和实际应用
2. 提供适度的技术细节
3. 展示实用的代码示例
4. 解释相关的编程原理
5. 解释深度：{explanation_depth:.1f}（适中详细）

请确保回答既有深度又实用。"""

        else:
            # 高级水平
            return f"""{base_prompt}
你正在教一个有经验的学习者。请用以下方式回答：
1. 深入探讨概念和原理
2. 讨论最佳实践和设计模式
3. 分析性能考量和权衡
4. 提供高级应用场景
5. 解释深度：{explanation_depth:.1f}（深入详细）

请确保回答专业、深入，满足高级学习者的需求。"""


class KnowledgeBaseRetrievalAgent:
    """知识库检索子代理 - 集成认知评估"""

    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.cognition_api = get_cognition_api()
        self._enhance_knowledge_base()

    def _enhance_knowledge_base(self):
        """增强知识库内容"""
        enhanced_knowledge = {
            "python_basics": [
                {
                    "question": "如何开始学习Python？",
                    "answer": "学习Python的建议路径：1. 先学习基础语法 2. 练习简单的程序 3. 学习常用数据结构 4. 尝试小项目",
                    "examples": ["推荐资源：Python官方文档、Codecademy、廖雪峰的Python教程"],
                    "difficulty_levels": {
                        "beginner": "从安装Python和运行第一个程序开始，学习基本语法和简单概念。",
                        "intermediate": "深入学习函数、模块和面向对象编程，开始构建小项目。",
                        "advanced": "探索高级特性如装饰器、生成器，并参与开源项目。"
                    }
                }
            ],
            "interactive_help": [
                {
                    "question": "系统能做什么？",
                    "answer": "我可以帮你：1. 回答编程问题 2. 生成练习题目 3. 评价你的代码 4. 提供个性化学习建议",
                    "examples": ["试试问我：'生成一个Python练习' 或 '评价我的代码'"],
                    "difficulty_levels": {
                        "beginner": "我会用简单的方式解释概念，帮助你建立信心。",
                        "intermediate": "我会提供实用的示例和练习，帮助你提升技能。",
                        "advanced": "我会深入讨论高级话题，帮助你成为专家。"
                    }
                }
            ]
        }

        for topic, items in enhanced_knowledge.items():
            for item in items:
                self.knowledge_base.add_knowledge(
                    topic, item["question"], item["answer"], item.get("examples", []),

                )

    async def retrieve_from_knowledge_base(self, question: str, user_id: str) -> Dict[str, Any]:
        """从知识库检索答案 - 基于认知水平个性化"""
        results = self.knowledge_base.search(question)

        if results:
            best_match = results[0]

            # 获取用户认知水平以个性化回答
            cognitive_level = await self.cognition_api.get_cognitive_level(user_id)
            personalized_answer = await self._personalize_knowledge_answer(
                best_match, cognitive_level
            )

            return {
                "found": True,
                "answer": personalized_answer,
                "examples": best_match.get("examples", []),
                "source": "knowledge_base",
                "confidence": "high",
                "personalized": True
            }
        else:
            return {"found": False, "answer": ""}

    async def _personalize_knowledge_answer(self, knowledge_item: Dict[str, Any],
                                            cognitive_level: Dict[str, Any]) -> str:
        """基于认知水平个性化知识库回答"""
        base_answer = knowledge_item["answer"]
        difficulty_levels = knowledge_item.get("metadata", {}).get("difficulty_levels", {})

        level = cognitive_level["overall_level"]

        if level < 0.4 and "beginner" in difficulty_levels:
            return f"{difficulty_levels['beginner']}\n\n{base_answer}"
        elif level < 0.7 and "intermediate" in difficulty_levels:
            return f"{difficulty_levels['intermediate']}\n\n{base_answer}"
        elif level >= 0.7 and "advanced" in difficulty_levels:
            return f"{difficulty_levels['advanced']}\n\n{base_answer}"
        else:
            return base_answer


class QAAgent(BaseAgent):
    """答疑代理 - 集成认知评估增强版"""

    def __init__(self, personal_agent):
        super().__init__("QAAgent")
        self.thinking_agent = ThinkingQAAgent()
        self.kb_agent = KnowledgeBaseRetrievalAgent()
        self.personal_agent = personal_agent
        self.cognition_api = get_cognition_api()

    async def answer_question(self, question: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """回答问题总入口 - 集成认知评估"""
        self.log_activity("开始处理问题", {"question": question, "user_id": user_id})

        # 记录交互开始时间
        start_time = asyncio.get_event_loop().time()

        # 首先尝试知识库检索
        kb_result = await self.kb_agent.retrieve_from_knowledge_base(question, user_id)

        if kb_result["found"] and kb_result["confidence"] == "high":
            self.log_activity("从知识库找到高质量答案")
            result = {
                "response": kb_result["answer"],
                "examples": kb_result.get("examples", []),
                "source": "knowledge_base",
                "needs_thinking": False,
                "personalized": kb_result.get("personalized", False)
            }
        else:
            # 复杂问题需要思考分析
            self.log_activity("使用思考代理处理问题")
            thinking_result = await self.thinking_agent.think_and_answer(question, user_id, context)

            result = {
                "response": thinking_result["answer"],
                "examples": [],
                "source": "llm_thinking",
                "needs_thinking": True,
                "cognitive_level_used": thinking_result["cognitive_level_used"],
                "personalized": thinking_result["personalization_applied"]
            }

        # 计算处理时间
        processing_time = asyncio.get_event_loop().time() - start_time

        # 记录认知评估数据
        await self._record_cognitive_data(user_id, question, result, processing_time)

        return result

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理答疑请求 - 集成认知评估"""
        question = request["content"]
        user_id = request["user_id"]

        # 回答问题
        result = await self.answer_question(question, user_id)

        # 提取主题用于用户画像
        topic = self._extract_topic(question)

        # 更新用户画像（记录提问行为）
        behavior_data = {
            "user_id": user_id,
            "question_type": "qa",
            "topic": topic,
            "complexity": "complex" if result["needs_thinking"] else "simple",
            "content": question[:100],  # 记录前100个字符
            "cognitive_level": result.get("cognitive_level_used", 0.5),
            "personalization_applied": result.get("personalized", False)
        }
        await self.personal_agent.track_user_behavior(behavior_data)

        # 获取认知洞察用于响应
        cognitive_insights = await self._get_cognitive_insights(user_id, topic)

        # 构建响应
        response_data = {
            "response": result["response"],
            "details": {
                "source": result["source"],
                "examples": result["examples"],
                "topic": topic,
                "answer_type": "detailed" if result["needs_thinking"] else "quick",
                "personalized": result.get("personalized", False),
                "cognitive_insights": cognitive_insights
            }
        }

        # 添加学习建议（基于认知评估）
        if result["needs_thinking"] or cognitive_insights.get("needs_improvement", False):
            learning_tips = await self._generate_cognitive_learning_tips(user_id, topic)
            response_data["details"]["learning_tips"] = learning_tips

        return response_data

    async def _record_cognitive_data(self, user_id: str, question: str, result: Dict[str, Any], processing_time: float):
        """记录认知评估数据"""
        try:
            interaction_data = {
                "processing_time": processing_time,
                "correctness": 0.8,  # QA场景中假设回答质量高
                "complexity": self._estimate_question_complexity(question),
                "domain": self._extract_knowledge_domain(question),
                "cognitive_level": "understand",  # QA主要涉及理解维度
                "explanation_depth": result.get("cognitive_level_used", 0.5),
                "response_quality": self._estimate_response_quality(result)
            }

            await self.cognition_api.record_interaction(
                user_id, "qa", interaction_data
            )

        except Exception as e:
            self.logger.warning(f"记录认知数据失败: {e}")

    async def _get_cognitive_insights(self, user_id: str, topic: str) -> Dict[str, Any]:
        """获取认知洞察"""
        try:
            cognitive_level = await self.cognition_api.get_cognitive_level(user_id)
            recommendations = await self.cognition_api.get_personalization_recommendations(user_id, "qa")

            # 分析当前主题的掌握情况
            topic_mastery = self._analyze_topic_mastery(cognitive_level, topic)

            return {
                "current_level": cognitive_level["overall_level"],
                "learning_velocity": cognitive_level.get("learning_velocity", 0.5),
                "topic_mastery": topic_mastery,
                "needs_improvement": topic_mastery < 0.6,
                "recommended_approach": recommendations.get("preferred_approach", "balanced"),
                "difficulty_level": recommendations.get("difficulty_level", "intermediate")
            }
        except Exception as e:
            self.logger.warning(f"获取认知洞察失败: {e}")
            return {}

    async def _generate_cognitive_learning_tips(self, user_id: str, topic: str) -> List[str]:
        """基于认知评估生成学习建议"""
        try:
            cognitive_insights = await self._get_cognitive_insights(user_id, topic)
            recommendations = await self.cognition_api.get_personalization_recommendations(user_id, "qa")

            tips = []

            # 基于认知水平添加建议
            level = cognitive_insights.get("current_level", 0.5)
            if level < 0.4:
                tips.extend([
                    "建议多练习基础概念，建立扎实的基础",
                    "尝试编写简单的程序来巩固理解",
                    "不要急于学习高级概念，先把基础打牢"
                ])
            elif level < 0.7:
                tips.extend([
                    "可以开始尝试更复杂的项目挑战",
                    "深入学习相关领域的核心概念",
                    "参与实际项目来应用所学知识"
                ])
            else:
                tips.extend([
                    "可以探索高级主题和最佳实践",
                    "考虑学习相关的设计模式和架构",
                    "参与开源项目或技术社区讨论"
                ])

            # 基于推荐方法添加建议
            approach = recommendations.get("preferred_approach", "")
            if approach == "challenge_based":
                tips.append("尝试解决一些有挑战性的编程问题")
            elif approach == "project_based":
                tips.append("通过实际项目来深化理解和应用")

            return tips

        except Exception as e:
            self.logger.warning(f"生成认知学习建议失败: {e}")
            return self._generate_learning_tips(topic)  # 回退到原有方法

    def _estimate_question_complexity(self, question: str) -> float:
        """估计问题复杂度"""
        complexity = 0.5

        # 基于问题长度
        if len(question) > 100:
            complexity += 0.2
        elif len(question) < 30:
            complexity -= 0.2

        # 基于技术关键词
        complex_keywords = ["继承", "多态", "递归", "算法", "复杂度", "设计模式", "架构"]
        if any(keyword in question for keyword in complex_keywords):
            complexity += 0.3

        return max(0.1, min(1.0, complexity))

    def _estimate_response_quality(self, result: Dict[str, Any]) -> float:
        """估计响应质量"""
        quality = 0.7  # 基础质量

        if result.get("personalized", False):
            quality += 0.2

        if result.get("needs_thinking", False):
            quality += 0.1

        return min(1.0, quality)

    def _analyze_topic_mastery(self, cognitive_level: Dict[str, Any], topic: str) -> float:
        """分析主题掌握程度"""
        # 基于认知维度和领域知识估计主题掌握度
        domain_mapping = {
            "python_basics": "syntax",
            "data_structures": "data_structures",
            "algorithms": "algorithms",
            "oop": "oop",
            "web_development": "syntax",  # 近似映射
            "data_science": "algorithms"  # 近似映射
        }

        domain = domain_mapping.get(topic, "syntax")
        domain_score = cognitive_level.get("knowledge_domains", {}).get(domain, 0.5)

        # 结合理解维度得分
        understanding_score = cognitive_level.get("cognitive_dimensions", {}).get("understand", 0.5)

        return (domain_score + understanding_score) / 2

    def _extract_topic(self, question: str) -> str:
        """从问题中提取主题 - 增强识别"""
        question_lower = question.lower()

        topic_keywords = {
            "python_basics": ["python", "函数", "def", "参数", "变量", "语法", "基础", "入门"],
            "data_structures": ["列表", "字典", "元组", "集合", "数组", "数据结构", "链表", "栈", "队列"],
            "algorithms": ["算法", "排序", "查找", "递归", "复杂度", "二分", "动态规划", "贪心"],
            "oop": ["类", "对象", "继承", "多态", "封装", "面向对象", "实例", "属性"],
            "web_development": ["网页", "网站", "flask", "django", "html", "css", "javascript", "前端"],
            "data_science": ["数据", "分析", "pandas", "numpy", "可视化", "机器学习", "深度学习", "分析"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                return topic

        return "general_programming"

    def _extract_knowledge_domain(self, question: str) -> str:
        """提取知识领域 - 用于认知评估"""
        topic = self._extract_topic(question)

        domain_mapping = {
            "python_basics": "syntax",
            "data_structures": "data_structures",
            "algorithms": "algorithms",
            "oop": "oop",
            "web_development": "syntax",
            "data_science": "algorithms",
            "general_programming": "syntax"
        }

        return domain_mapping.get(topic, "syntax")

    async def _generate_learning_tips(self, topic: str) -> List[str]:
        """生成学习建议 - 保留原有方法作为回退"""
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