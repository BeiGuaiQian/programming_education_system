# src/programming_education_system/agents/qa_agent.py
"""
答疑代理 - 完全使用科学认知API版本
"""
from typing import Dict, Any, List
import logging
import asyncio

from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.models.knowledge_base import KnowledgeBase
from programming_education_system.agents.base_agent import BaseAgent

# 导入科学认知API
from programming_education_system.cognition_judger.cognitive_api_scientific import get_scientific_cognitive_api, get_scientific_cognitive_api_sync

logger = logging.getLogger(__name__)


class ThinkingQAAgent:
    """思考答疑子代理 - 科学认知API版本"""

    def __init__(self):
        self.name = "ThinkingQAAgent"
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def think_and_answer(self, complex_question: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理复杂问题分析 - 基于科学认知水平个性化"""

        # 获取用户认知状态和个性化参数
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        learning_params = await self.cognition_api.get_personalized_learning_parameters(user_id, "explanation")

        # 基于认知状态调整系统提示
        system_prompt = self._build_system_prompt(cognitive_state, learning_params)

        user_message = f"学习者提问：{complex_question}"

        if context:
            user_message += f"\n学习上下文：{context}"

        user_message += "\n\n请用适合学习者水平的方式回答这个问题："

        # 生成回答
        answer = await llm_client.generate_response(system_prompt, user_message)

        return {
            "answer": answer,
            "cognitive_level_used": cognitive_state["overall_cognitive_level"],
            "learning_parameters": learning_params,
            "personalization_applied": True
        }

    def _build_system_prompt(self, cognitive_state: Dict[str, Any], learning_params: Dict[str, Any]) -> str:
        """基于认知状态构建系统提示"""

        cognitive_level = cognitive_state["overall_cognitive_level"]
        parameters = learning_params.get("parameters", {})
        explanation_depth = parameters.get("explanation_depth", 0.7)
        learning_chars = cognitive_state.get("learning_characteristics", {})

        base_prompt = "你是一个耐心、专业的编程教育专家，擅长根据学习者的认知水平调整解释方式。你需要结合主代理给你的要求完成答疑任务"

        if cognitive_level < 0.4:
            # 初学者级别
            return f"""{base_prompt}
你正在教一个编程初学者。请用以下方式回答：
1. 使用简单易懂的语言，避免专业术语
2. 提供具体的、一步一步的解释
3. 多用类比和生活化的例子
4. 鼓励学习者，给予正面反馈
5. 解释深度：{explanation_depth:.1f}（较浅显易懂）

学习特征：{learning_chars.get('learning_style', 'balanced')}
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

学习特征：{learning_chars.get('learning_style', 'balanced')}
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

学习特征：{learning_chars.get('learning_style', 'balanced')}
请确保回答专业、深入，满足高级学习者的需求。"""


class KnowledgeBaseRetrievalAgent:
    """知识库检索子代理 - 科学认知API版本"""

    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.cognition_api = get_scientific_cognitive_api_sync()
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
        """从知识库检索答案 - 基于科学认知状态个性化"""
        results = self.knowledge_base.search(question)

        if results:
            best_match = results[0]

            # 获取用户认知状态以个性化回答
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
            personalized_answer = await self._personalize_knowledge_answer(
                best_match, cognitive_state
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
                                            cognitive_state: Dict[str, Any]) -> str:
        """基于认知状态个性化知识库回答"""
        base_answer = knowledge_item["answer"]
        difficulty_levels = knowledge_item.get("metadata", {}).get("difficulty_levels", {})

        level = cognitive_state["overall_cognitive_level"]
        learning_trend = cognitive_state.get("learning_trend", "stable")

        # 基于认知水平和学习趋势选择回答
        if level < 0.4 and "beginner" in difficulty_levels:
            personalized = difficulty_levels['beginner']
        elif level < 0.7 and "intermediate" in difficulty_levels:
            personalized = difficulty_levels['intermediate']
        elif level >= 0.7 and "advanced" in difficulty_levels:
            personalized = difficulty_levels['advanced']
        else:
            personalized = base_answer

        # 基于学习趋势添加额外指导
        if learning_trend == "improving":
            personalized += "\n\n💪 看起来你在进步！继续保持这个学习节奏。"
        elif learning_trend == "declining":
            personalized += "\n\n🤔 如果觉得困难，可以回顾一下基础概念，或者尝试更简单的练习。"

        return f"{personalized}\n\n{base_answer}"


class QAAgent(BaseAgent):
    """答疑代理 - 科学认知API版本"""

    def __init__(self, personal_agent):
        super().__init__("QAAgent")
        self.thinking_agent = ThinkingQAAgent()
        self.kb_agent = KnowledgeBaseRetrievalAgent()
        self.personal_agent = personal_agent
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def answer_question(self, question: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """回答问题总入口 - 集成科学认知评估"""
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
                "personalized": thinking_result["personalization_applied"],
                "learning_parameters": thinking_result.get("learning_parameters", {})
            }

        # 计算处理时间
        processing_time = asyncio.get_event_loop().time() - start_time

        # 记录科学认知评估数据
        await self._record_scientific_cognitive_data(user_id, question, result, processing_time)

        return result

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理答疑请求 - 集成科学认知评估"""
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

        # 获取科学认知洞察用于响应
        cognitive_insights = await self._get_scientific_cognitive_insights(user_id, topic)

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

        # 添加学习建议（基于科学认知评估）
        if result["needs_thinking"] or cognitive_insights.get("needs_improvement", False):
            learning_tips = await self._generate_scientific_learning_tips(user_id, topic)
            response_data["details"]["learning_tips"] = learning_tips

        return response_data

    async def _record_scientific_cognitive_data(self, user_id: str, question: str, result: Dict[str, Any], processing_time: float):
        """记录科学认知评估数据"""
        try:
            # 构建交互数据
            interaction_data = {
                'type': 'qa',
                'content': question,
                'user_response': result.get('response', ''),
                'processing_time': processing_time,
                'context': '答疑交互',
                'metadata': {
                    'code_quality': 0.7,
                    'explanation_quality': 0.7,
                    'response_length': len(result.get('response', '')),
                    'success': True,
                    'interaction_type': 'qa'
                }
            }

            # 使用科学API方法
            analysis_result = await self.cognition_api.analyze_learning_interaction(user_id, interaction_data)

            if analysis_result['success']:
                self.logger.info(f"科学认知分析完成")
            else:
                self.logger.warning(f"科学认知分析部分失败: {analysis_result.get('error', '未知错误')}")

        except Exception as e:
            self.logger.warning(f"记录科学认知数据失败: {e}")

    async def _get_scientific_cognitive_insights(self, user_id: str, topic: str) -> Dict[str, Any]:
        """获取科学认知洞察 - 修复方法调用"""
        try:
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)

            # 获取学习推荐
            learning_recs = await self.cognition_api.get_learning_recommendations(user_id, f"学习{topic}")

            # 分析当前主题的掌握情况
            topic_mastery = self._analyze_topic_mastery(cognitive_state, topic)

            return {
                "current_level": cognitive_state["overall_cognitive_level"],
                "learning_trend": cognitive_state.get("learning_trend", "stable"),
                "topic_mastery": topic_mastery,
                "needs_improvement": topic_mastery < 0.6,
                "recommended_difficulty": learning_recs.get('recommendations', {}).get('recommended_difficulty', 'intermediate'),
                "focus_areas": learning_recs.get('recommendations', {}).get('focus_areas', [])
            }
        except Exception as e:
            self.logger.warning(f"获取科学认知洞察失败: {e}")
            return {}

    async def _generate_scientific_learning_tips(self, user_id: str, topic: str) -> List[str]:
        """基于科学认知评估生成学习建议"""
        try:
            cognitive_insights = await self._get_scientific_cognitive_insights(user_id, topic)
            learning_recs = await self.cognition_api.get_learning_recommendations(user_id, f"掌握{topic}")

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

            # 基于学习推荐添加建议
            recommendations = learning_recs.get('recommendations', {})
            if 'suggested_topics' in recommendations:
                next_topics = recommendations['suggested_topics'][:2]
                tips.append(f"接下来可以学习: {', '.join(next_topics)}")

            return tips

        except Exception as e:
            self.logger.warning(f"生成科学学习建议失败: {e}")
            return self._generate_learning_tips(topic)

    def _analyze_topic_mastery(self, cognitive_state: Dict[str, Any], topic: str) -> float:
        """分析主题掌握程度"""
        knowledge_domains = cognitive_state.get("knowledge_domains", {})

        # 映射主题到知识领域
        topic_to_domain = {
            "python_basics": "python_basics",
            "data_structures": "data_structures",
            "algorithms": "algorithms",
            "oop": "oop",
            "web_development": "python_basics",
            "data_science": "algorithms"
        }

        domain = topic_to_domain.get(topic, "python_basics")
        domain_score = knowledge_domains.get(domain, 0.5)

        # 结合理解维度得分
        cognitive_dimensions = cognitive_state.get("cognitive_dimensions", {})
        understanding_score = cognitive_dimensions.get("understand", 0.5)

        return (domain_score + understanding_score) / 2

    def _extract_topic(self, question: str) -> str:
        """从问题中提取主题"""
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

    def _generate_learning_tips(self, topic: str) -> List[str]:
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