# src/programming_education_system/agents/exercise_agent.py
"""
练习生成代理 - 增强版
优先遵循用户明确要求，结合个性化认知数据，改进题目保存和答案检索
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import asyncio
import json
import time
import hashlib
import re
from datetime import datetime
from collections import defaultdict

from programming_education_system.models.question_bank import QuestionBank, DifficultyLevel, QuestionType
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

# 导入科学认知API
from programming_education_system.cognition_judger.cognitive_api_scientific import get_scientific_cognitive_api, \
    get_scientific_cognitive_api_sync

logger = logging.getLogger(__name__)

# src/programming_education_system/agents/exercise_agent.py
"""
练习生成代理 - 增强版
完整的EnhancedQuestionBankManager类
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import asyncio
import json
import time
import hashlib
import re
from datetime import datetime
from collections import defaultdict

from programming_education_system.models.question_bank import QuestionBank, DifficultyLevel, QuestionType
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

# 导入科学认知API
from programming_education_system.cognition_judger.cognitive_api_scientific import get_scientific_cognitive_api, \
    get_scientific_cognitive_api_sync

logger = logging.getLogger(__name__)


class EnhancedQuestionBankManager:
    """增强版题库管理器 - 支持时间排序和用户个性化管理"""

    def __init__(self):
        self.question_bank = QuestionBank()
        self.user_question_history = defaultdict(list)  # 用户ID -> 题目历史列表（按时间排序）
        self.cognition_api = get_scientific_cognitive_api_sync()

        # 初始化示例题目
        self._initialize_sample_questions()

    def _initialize_sample_questions(self):
        """如果题库为空，初始化示例题目"""
        try:
            stats = self.question_bank.get_statistics()
            if stats.get('total_questions', 0) == 0:
                logger.info("检测到空题库，正在初始化示例题目...")
                self._add_sample_questions()
        except Exception as e:
            logger.warning(f"检查题库状态失败: {e}")

    def _add_sample_questions(self):
        """添加示例题目"""
        sample_questions = [
            {
                "topic": "python_basics",
                "content": "编写一个函数，接受两个数字参数并返回它们的和。",
                "difficulty": DifficultyLevel.BEGINNER,
                "question_type": QuestionType.CODING,
                "answer": "def add(a, b):\n    return a + b",
                "hints": ["使用def关键字定义函数", "使用return语句返回结果"],
                "examples": [
                    {"input": "add(2, 3)", "output": "5"},
                    {"input": "add(-1, 1)", "output": "0"}
                ],
                "tags": ["函数", "基础"],
                "source": "system"
            },
            {
                "topic": "python_basics",
                "content": "编写一个函数，判断一个数字是否为偶数。",
                "difficulty": DifficultyLevel.BEGINNER,
                "question_type": QuestionType.CODING,
                "answer": "def is_even(n):\n    return n % 2 == 0",
                "hints": ["使用取模运算符%", "偶数除以2的余数为0"],
                "examples": [
                    {"input": "is_even(4)", "output": "True"},
                    {"input": "is_even(7)", "output": "False"}
                ],
                "tags": ["函数", "条件判断"],
                "source": "system"
            },
            {
                "topic": "python_basics",
                "content": "编写一个函数，计算列表中所有元素的平均值。",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "question_type": QuestionType.CODING,
                "answer": "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)",
                "hints": ["使用sum函数计算总和", "使用len函数获取元素个数", "注意空列表的情况"],
                "examples": [
                    {"input": "calculate_average([1, 2, 3, 4, 5])", "output": "3.0"},
                    {"input": "calculate_average([])", "output": "0"}
                ],
                "tags": ["列表", "数学计算"],
                "source": "system"
            },
            {
                "topic": "data_structures",
                "content": "实现一个栈类，包含push、pop和peek方法。",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "question_type": QuestionType.CODING,
                "answer": "class Stack:\n    def __init__(self):\n        self.items = []\n    \n    def push(self, item):\n        self.items.append(item)\n    \n    def pop(self):\n        if self.is_empty():\n            return None\n        return self.items.pop()\n    \n    def peek(self):\n        if self.is_empty():\n            return None\n        return self.items[-1]\n    \n    def is_empty(self):\n        return len(self.items) == 0",
                "hints": ["使用列表作为底层存储", "注意处理空栈的情况"],
                "examples": [
                    {"input": "stack = Stack(); stack.push(1); stack.push(2); stack.pop()", "output": "2"},
                    {"input": "stack = Stack(); stack.peek()", "output": "None"}
                ],
                "tags": ["栈", "数据结构"],
                "source": "system"
            }
        ]

        for question_data in sample_questions:
            self.question_bank.add_question(**question_data)

    def _generate_question_hash(self, question_content: Dict[str, Any]) -> str:
        """生成唯一的题目内容哈希值"""
        content_str = (
            f"{question_content.get('title', '')}"
            f"{question_content.get('description', '')}"
            f"{''.join(question_content.get('requirements', []))}"
            f"{str(question_content.get('examples', []))}"
            f"{str(question_content.get('hints', []))}"
            f"{question_content.get('difficulty', '')}"
            f"{str(time.time())}"
        )
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()[:16]

    async def find_matching_questions(self, user_id: str, topic: str = None,
                                      difficulty: str = None, limit: int = 5,
                                      exclude_recent: bool = True) -> List[Dict[str, Any]]:
        """查找匹配的题目，支持排除最近题目"""
        try:
            # 转换难度级别
            difficulty_enum = None
            if difficulty:
                difficulty_map = {
                    "beginner": DifficultyLevel.BEGINNER,
                    "intermediate": DifficultyLevel.INTERMEDIATE,
                    "advanced": DifficultyLevel.ADVANCED
                }
                difficulty_enum = difficulty_map.get(difficulty)

            # 从题库获取题目
            questions = self.question_bank.get_questions_by_filters(
                topic=topic,
                difficulty=difficulty_enum,
                limit=limit * 3  # 获取更多用于过滤
            )

            # 获取用户最近见过的题目
            recent_question_hashes = set()
            if exclude_recent:
                user_history = self.get_user_question_history(user_id)
                recent_question_hashes = {q.get('hash') for q in user_history[:10] if q.get('hash')}

            # 转换格式并过滤
            result_questions = []
            for q in questions:
                question_content = {
                    "title": f"题库题目 - {q.topic}",
                    "description": q.content,
                    "requirements": ["完成题目要求"],
                    "examples": q.examples or [{"input": "示例输入", "output": "示例输出"}],
                    "hints": q.hints or ["从简单功能开始", "注意边界条件"],
                    "difficulty": q.difficulty.value
                }
                question_hash = self._generate_question_hash(question_content)

                if question_hash not in recent_question_hashes:
                    question_data = {
                        "id": q.id,
                        "question_id": f"bank_{q.id}",
                        "type": q.question_type.value,
                        "topic": q.topic,
                        "difficulty": q.difficulty.value,
                        "content": question_content,
                        "source": "question_bank",
                        "hash": question_hash,
                        "timestamp": time.time(),
                        "created_at": datetime.now().isoformat()
                    }
                    result_questions.append(question_data)

                    if len(result_questions) >= limit:
                        break

            return result_questions

        except Exception as e:
            logger.error(f"查找匹配题目失败: {e}")
            return []

    async def save_generated_question(self, user_id: str, question_data: Dict[str, Any]) -> str:
        """保存生成的题目到题库并记录用户历史"""
        try:
            content = question_data['content']

            # 生成题目哈希
            question_hash = self._generate_question_hash(content)

            # 检查是否已存在
            existing_hashes = {q.get('hash') for q in self.user_question_history.get(user_id, [])}
            if question_hash in existing_hashes:
                return question_hash

            # 转换难度级别
            difficulty_map = {
                "beginner": DifficultyLevel.BEGINNER,
                "intermediate": DifficultyLevel.INTERMEDIATE,
                "advanced": DifficultyLevel.ADVANCED
            }
            difficulty_enum = difficulty_map.get(question_data.get('difficulty', 'intermediate'),
                                                 DifficultyLevel.INTERMEDIATE)

            # 保存到题库
            question_id = self.question_bank.add_question(
                topic=question_data.get('topic', 'general'),
                content=content['description'],
                difficulty=difficulty_enum,
                question_type=QuestionType.CODING,
                answer=content.get('answer', ''),
                hints=content.get('hints', []),
                examples=content.get('examples', []),
                tags=question_data.get('cognitive_focus', []),
                source="ai_generated"
            )

            # 记录到用户历史
            history_entry = {
                "question_id": f"generated_{question_id}",
                "hash": question_hash,
                "topic": question_data.get('topic', 'general'),
                "difficulty": question_data.get('difficulty', 'intermediate'),
                "description": content.get('description', '')[:200],
                "content": content,
                "timestamp": time.time(),
                "created_at": datetime.now().isoformat(),
                "source": "ai_generated"
            }

            self.user_question_history[user_id].append(history_entry)
            # 按时间排序，最新的在前面
            self.user_question_history[user_id].sort(key=lambda x: x['timestamp'], reverse=True)
            # 只保留最近100条记录
            self.user_question_history[user_id] = self.user_question_history[user_id][:100]

            logger.info(f"已保存生成题目到题库: {question_id}, 用户: {user_id}")
            return question_hash

        except Exception as e:
            logger.error(f"保存生成题目失败: {e}")
            return ""

    def get_user_question_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户题目历史（按时间倒序）"""
        history = self.user_question_history.get(user_id, [])
        return history[:limit]

    def get_recent_questions_by_topic(self, user_id: str, topic: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """按主题获取用户最近的题目"""
        history = self.user_question_history.get(user_id, [])
        if topic:
            filtered = [q for q in history if q.get('topic') == topic]
        else:
            filtered = history
        return filtered[:limit]

    def update_question_usage(self, question_id: int, success: bool = True):
        """更新题目使用统计"""
        try:
            self.question_bank.update_question_usage(question_id, success)
        except Exception as e:
            logger.error(f"更新题目使用统计失败: {e}")

    def search_questions_by_content(self, content: str, user_id: str = None, limit: int = 10,
                                    max_search_count: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """
        根据题目内容搜索题目，优先查找最近存储的题目

        Args:
            content: 题目内容（可能不完整）
            user_id: 用户ID，用于优先搜索用户历史
            limit: 返回结果数量限制
            max_search_count: 最大搜索数量限制

        Returns:
            (匹配的题目列表, 实际搜索的题目数量)
        """
        try:
            matched_questions = []
            searched_count = 0

            # 1. 优先从用户最近的历史题目中搜索
            if user_id:
                user_history = self.get_user_question_history(user_id, limit=max_search_count)
                searched_count += len(user_history)

                for question in user_history:
                    if self._is_content_similar(content, question):
                        matched_questions.append(question)
                        if len(matched_questions) >= limit:
                            break

            # 2. 如果用户历史中没找到足够题目，从题库中搜索
            if len(matched_questions) < limit and searched_count < max_search_count:
                remaining_limit = min(limit - len(matched_questions), max_search_count - searched_count)

                # 获取题库题目，按时间倒序（假设新题目ID更大）
                all_questions = self.question_bank.get_questions_by_filters(limit=max_search_count)
                # 按ID倒序排序，假设ID越大题目越新
                all_questions.sort(key=lambda x: x.id, reverse=True)

                for question in all_questions[:remaining_limit]:
                    searched_count += 1
                    question_dict = self._question_to_dict(question)
                    if self._is_content_similar(content, question_dict):
                        matched_questions.append(question_dict)
                        if len(matched_questions) >= limit:
                            break

            return matched_questions, searched_count

        except Exception as e:
            logger.error(f"搜索题目失败: {e}")
            return [], 0

    def _is_content_similar(self, partial_content: str, question: Dict[str, Any]) -> bool:
        """
        判断部分内容是否与题目相似
        使用简单的文本匹配算法
        """
        try:
            # 提取题目的关键文本
            question_text = ""
            if 'content' in question and isinstance(question['content'], dict):
                content_dict = question['content']
                question_text += content_dict.get('title', '') + " "
                question_text += content_dict.get('description', '') + " "
                question_text += " ".join(content_dict.get('requirements', []))
            else:
                question_text = str(question.get('description', '')) + " " + str(question.get('content', ''))

            # 清理文本
            question_text = self._clean_text(question_text)
            partial_content = self._clean_text(partial_content)

            # 如果部分内容完全包含在题目文本中，认为是匹配的
            if partial_content in question_text:
                return True

            # 计算关键词重叠率
            partial_words = set(partial_content.split())
            question_words = set(question_text.split())

            if not partial_words:
                return False

            overlap = partial_words.intersection(question_words)
            overlap_ratio = len(overlap) / len(partial_words)

            # 如果关键词重叠率超过50%，认为是相似的
            return overlap_ratio >= 0.5

        except Exception as e:
            logger.warning(f"内容相似度判断失败: {e}")
            return False

    def _clean_text(self, text: str) -> str:
        """清理文本，移除特殊字符和多余空格"""
        # 移除特殊字符，保留中文、英文、数字和基本标点
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\s\.\?\!,，。！？]', ' ', str(text))
        # 合并多个空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip().lower()

    def _question_to_dict(self, question) -> Dict[str, Any]:
        """将Question对象转换为字典"""
        return {
            "id": question.id,
            "question_id": f"bank_{question.id}",
            "type": question.question_type.value,
            "topic": question.topic,
            "difficulty": question.difficulty.value,
            "content": {
                "title": f"题库题目 - {question.topic}",
                "description": question.content,
                "requirements": ["完成题目要求"],
                "examples": question.examples or [{"input": "示例输入", "output": "示例输出"}],
                "hints": question.hints or ["从简单功能开始", "注意边界条件"],
                "difficulty": question.difficulty.value,
                "answer": getattr(question, 'answer', '')  # 确保包含答案
            },
            "source": "question_bank",
            "hash": self._generate_question_hash({
                "title": f"题库题目 - {question.topic}",
                "description": question.content,
                "requirements": ["完成题目要求"],
                "examples": question.examples or [{"input": "示例输入", "output": "示例输出"}],
                "hints": question.hints or ["从简单功能开始", "注意边界条件"],
                "difficulty": question.difficulty.value
            }),
            "timestamp": time.time(),
            "created_at": datetime.now().isoformat()
        }

    def get_question_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """获取题目统计信息"""
        try:
            # 获取题库统计
            bank_stats = self.question_bank.get_statistics()

            # 获取用户历史统计
            user_stats = {}
            if user_id:
                user_history = self.get_user_question_history(user_id)
                user_stats = {
                    "total_questions_attempted": len(user_history),
                    "recent_activity_count": len(
                        [q for q in user_history if q.get('timestamp', 0) > time.time() - 24 * 60 * 60]),
                    "favorite_topics": self._get_user_favorite_topics(user_id)
                }

            return {
                "question_bank": bank_stats,
                "user_specific": user_stats,
                "total_users_tracked": len(self.user_question_history)
            }
        except Exception as e:
            logger.error(f"获取题目统计失败: {e}")
            return {}

    def _get_user_favorite_topics(self, user_id: str) -> List[str]:
        """获取用户最常练习的主题"""
        try:
            user_history = self.get_user_question_history(user_id)
            topic_counts = {}

            for question in user_history:
                topic = question.get('topic', 'unknown')
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # 按练习次数排序，返回前3个
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            return [topic for topic, count in sorted_topics[:3]]

        except Exception as e:
            logger.warning(f"获取用户偏好主题失败: {e}")
            return []

    def clear_user_history(self, user_id: str):
        """清除用户历史记录"""
        try:
            if user_id in self.user_question_history:
                del self.user_question_history[user_id]
                logger.info(f"已清除用户 {user_id} 的题目历史")
        except Exception as e:
            logger.error(f"清除用户历史失败: {e}")

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """导出用户数据"""
        try:
            user_history = self.get_user_question_history(user_id)
            statistics = self.get_question_statistics(user_id)

            return {
                "user_id": user_id,
                "export_time": datetime.now().isoformat(),
                "total_questions": len(user_history),
                "question_history": user_history,
                "statistics": statistics
            }
        except Exception as e:
            logger.error(f"导出用户数据失败: {e}")
            return {}
class UserRequirementParser:
    """用户需求解析器 - 优先解析用户明确要求"""

    def __init__(self):
        self.difficulty_keywords = {
            "beginner": ["简单", "基础", "入门", "beginner", "easy", "初级", "基础"],
            "intermediate": ["中等", "普通", "intermediate", "medium", "中级", "一般"],
            "advanced": ["难", "高级", "复杂", "advanced", "hard", "高级", "困难"]
        }

        self.quantity_keywords = {
            "single": ["一道", "一个", "1个", "1道", "single", "one"],
            "multiple": ["多道", "多个", "一些", "几个", "multiple", "some", "几道"],
            "quiz": ["测验", "测试", "quiz", "exam", "考试", "一套"]
        }

        self.freshness_keywords = {
            "new": ["新", "重新", "换一个", "另一个", "new", "another", "不一样", "不同"],
            "similar": ["类似", "相似", "同样", "same", "similar", "一样"]
        }

    def parse_user_requirements(self, user_request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """解析用户明确要求"""
        request_lower = user_request.lower()
        requirements = {
            'explicit_topic': None,
            'explicit_difficulty': None,
            'quantity': 'single',  # 默认一道题
            'freshness': 'new',  # 默认新题目
            'exercise_type': 'practice',  # 练习类型
            'user_specific_requirements': []
        }

        # 解析主题
        requirements['explicit_topic'] = self._parse_explicit_topic(request_lower)

        # 解析难度
        requirements['explicit_difficulty'] = self._parse_explicit_difficulty(request_lower)

        # 解析数量
        requirements['quantity'] = self._parse_quantity(request_lower)

        # 解析新鲜度要求
        requirements['freshness'] = self._parse_freshness(request_lower)

        # 解析练习类型
        requirements['exercise_type'] = self._parse_exercise_type(request_lower)

        # 提取用户特定要求
        requirements['user_specific_requirements'] = self._extract_specific_requirements(user_request)

        # 从上下文获取补充信息
        if context:
            requirements.update(self._extract_context_requirements(context))

        logger.info(f"解析用户需求结果: {requirements}")
        return requirements

    def _parse_explicit_topic(self, request_lower: str) -> Optional[str]:
        """解析用户明确指定的主题"""
        topic_keywords = {
            "python_basics": ["python", "基础", "语法", "变量", "函数", "入门"],
            "data_structures": ["数据结构", "列表", "字典", "元组", "集合", "数组", "链表"],
            "algorithms": ["算法", "排序", "查找", "递归", "复杂度", "二分", "动态规划"],
            "oop": ["面向对象", "类", "对象", "继承", "多态", "封装", "oop"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                return topic
        return None

    def _parse_explicit_difficulty(self, request_lower: str) -> Optional[str]:
        """解析用户明确指定的难度"""
        for difficulty, keywords in self.difficulty_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                return difficulty
        return None

    def _parse_quantity(self, request_lower: str) -> str:
        """解析用户要求的题目数量"""
        for quantity_type, keywords in self.quantity_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                return quantity_type
        return 'single'

    def _parse_freshness(self, request_lower: str) -> str:
        """解析用户对题目新鲜度的要求"""
        for freshness, keywords in self.freshness_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                return freshness
        return 'new'

    def _parse_exercise_type(self, request_lower: str) -> str:
        """解析练习类型"""
        if any(word in request_lower for word in ["测验", "测试", "quiz", "exam"]):
            return "quiz"
        elif any(word in request_lower for word in ["复习", "回顾", "review"]):
            return "review"
        else:
            return "practice"

    def _extract_specific_requirements(self, user_request: str) -> List[str]:
        """提取用户特定要求"""
        requirements = []
        specific_patterns = [
            ("实现", "功能实现"),
            ("优化", "性能优化"),
            ("调试", "代码调试"),
            ("理解", "概念理解"),
            ("记忆", "知识记忆"),
            ("分析", "问题分析")
        ]

        for pattern, req_type in specific_patterns:
            if pattern in user_request:
                requirements.append(req_type)

        return requirements

    def _extract_context_requirements(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文中提取补充需求"""
        context_requirements = {}

        # 从对话历史中提取信息
        recent_history = context.get('recent_history', [])
        if recent_history:
            # 分析最近的主题偏好
            recent_topics = [h.get('topic') for h in recent_history if h.get('topic')]
            if recent_topics:
                context_requirements['recent_topic'] = max(set(recent_topics), key=recent_topics.count)

        # 从增强上下文中提取信息
        enhanced_context = context.get('enhanced_context', {})
        if enhanced_context.get('exercise_context'):
            context_requirements['current_exercise_context'] = enhanced_context['exercise_context']

        return context_requirements


class EnhancedExerciseGenerator:
    """增强版练习生成器 - 优先用户要求，辅助认知数据"""

    def __init__(self):
        self.cognition_api = get_scientific_cognitive_api_sync()
        self.question_bank_manager = EnhancedQuestionBankManager()
        self.requirement_parser = UserRequirementParser()

    async def generate_exercise_with_priority(self, user_id: str, user_request: str,
                                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """基于用户优先要求和认知辅助生成练习"""

        # 解析用户明确要求
        user_requirements = self.requirement_parser.parse_user_requirements(user_request, context)

        # 获取用户认知状态
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        user_level = cognitive_state["overall_cognitive_level"]

        # 确定最终参数：优先用户明确要求，其次认知数据
        final_topic = self._determine_topic(user_requirements, context)
        final_difficulty = self._determine_difficulty(user_requirements, user_level)
        final_quantity = self._determine_quantity(user_requirements)
        require_fresh = user_requirements['freshness'] == 'new'

        logger.info(f"最终生成参数: topic={final_topic}, difficulty={final_difficulty}, "
                    f"quantity={final_quantity}, fresh={require_fresh}")

        # 根据要求生成练习
        if user_requirements['exercise_type'] == 'quiz':
            return await self._generate_quiz(user_id, final_topic, final_difficulty, final_quantity)
        else:
            return await self._generate_practice_exercises(
                user_id, final_topic, final_difficulty, final_quantity,
                require_fresh, user_requirements, cognitive_state, user_request
            )

    def _determine_topic(self, user_requirements: Dict[str, Any], context: Dict[str, Any]) -> str:
        """确定主题：优先用户明确要求"""
        if user_requirements['explicit_topic']:
            return user_requirements['explicit_topic']

        # 从上下文中获取主题
        if context and context.get('recent_history'):
            recent_topics = [h.get('topic') for h in context['recent_history'] if h.get('topic')]
            if recent_topics:
                return max(set(recent_topics), key=recent_topics.count)

        return 'python_basics'  # 默认主题

    def _determine_difficulty(self, user_requirements: Dict[str, Any], user_level: float) -> str:
        """确定难度：优先用户明确要求"""
        if user_requirements['explicit_difficulty']:
            return user_requirements['explicit_difficulty']

        # 基于认知水平确定难度
        if user_level < 0.4:
            return "beginner"
        elif user_level < 0.7:
            return "intermediate"
        else:
            return "advanced"

    def _determine_quantity(self, user_requirements: Dict[str, Any]) -> int:
        """确定题目数量"""
        quantity_map = {
            'single': 1,
            'multiple': 3,
            'quiz': 5
        }
        return quantity_map.get(user_requirements['quantity'], 1)

    async def _generate_quiz(self, user_id: str, topic: str, difficulty: str, quantity: int) -> Dict[str, Any]:
        """生成测验"""
        try:
            questions = await self.question_bank_manager.find_matching_questions(
                user_id, topic, difficulty, quantity, exclude_recent=True
            )

            if len(questions) < quantity:
                # 补充生成题目
                needed = quantity - len(questions)
                additional_questions = await self._generate_new_questions(
                    user_id, topic, difficulty, needed, "测验题目"
                )
                questions.extend(additional_questions)

            return {
                "success": True,
                "type": "quiz",
                "questions": questions,
                "source": "mixed",
                "personalized": True,
                "user_requirements_met": True
            }

        except Exception as e:
            logger.error(f"生成测验失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _generate_practice_exercises(self, user_id: str, topic: str, difficulty: str,
                                           quantity: int, require_fresh: bool,
                                           user_requirements: Dict[str, Any],
                                           cognitive_state: Dict[str, Any],
                                           user_request: str) -> Dict[str, Any]:
        """生成练习题目"""
        try:
            questions = []

            # 如果不要求全新题目，先尝试从题库获取
            if not require_fresh:
                library_questions = await self.question_bank_manager.find_matching_questions(
                    user_id, topic, difficulty, quantity, exclude_recent=False
                )
                questions.extend(library_questions)

            # 如果数量不足或要求新题目，生成新题目
            if len(questions) < quantity or require_fresh:
                needed = quantity - len(questions) if not require_fresh else quantity
                new_questions = await self._generate_new_questions(
                    user_id, topic, difficulty, needed, user_request,
                    user_requirements, cognitive_state
                )
                questions.extend(new_questions)

            return {
                "success": True,
                "type": "practice",
                "questions": questions[:quantity],  # 确保不超过要求数量
                "source": "mixed",
                "personalized": True,
                "user_requirements_met": True,
                "requirements_analysis": {
                    "explicit_topic_used": user_requirements['explicit_topic'] is not None,
                    "explicit_difficulty_used": user_requirements['explicit_difficulty'] is not None,
                    "freshness_respected": require_fresh
                }
            }

        except Exception as e:
            logger.error(f"生成练习失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _generate_new_questions(self, user_id: str, topic: str, difficulty: str,
                                      quantity: int, user_request: str,
                                      user_requirements: Dict[str, Any] = None,
                                      cognitive_state: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """生成新题目"""
        questions = []

        for i in range(quantity):
            exercise = await self._create_personalized_exercise(
                user_id, topic, difficulty, user_request, user_requirements, cognitive_state
            )

            if exercise:
                # 保存到题库
                question_hash = await self.question_bank_manager.save_generated_question(user_id, exercise)
                if question_hash:
                    question_data = {
                        "question_id": f"generated_{int(time.time())}_{i}",
                        "type": "generated",
                        "topic": topic,
                        "difficulty": difficulty,
                        "content": exercise['content'],
                        "source": "ai_generated",
                        "hash": question_hash,
                        "timestamp": time.time(),
                        "created_at": datetime.now().isoformat()
                    }
                    questions.append(question_data)

        return questions

    async def _create_personalized_exercise(self, user_id: str, topic: str, difficulty: str,
                                            user_request: str, user_requirements: Dict[str, Any],
                                            cognitive_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建个性化练习题目"""
        try:
            # 获取学习推荐
            learning_recs = await self.cognition_api.get_learning_recommendations(user_id, topic)
            learning_params = await self.cognition_api.get_personalized_learning_parameters(user_id, "practice")

            # 识别认知薄弱维度
            weak_dimensions = self._identify_weak_cognitive_dimensions(cognitive_state)

            # 构建个性化提示
            system_prompt = self._build_personalized_system_prompt(
                topic, difficulty, user_request, user_requirements,
                weak_dimensions, cognitive_state["overall_cognitive_level"]
            )

            user_message = self._build_exercise_creation_message(
                topic, difficulty, user_requirements, weak_dimensions,
                cognitive_state["overall_cognitive_level"]
            )

            generated_content = await llm_client.generate_response(system_prompt, user_message)

            # 解析生成的练习内容
            exercise_data = self._parse_exercise_content(generated_content, topic, difficulty)

            return {
                "type": "personalized",
                "topic": topic,
                "difficulty": difficulty,
                "content": exercise_data,
                "cognitive_focus": weak_dimensions,
                "user_request": user_request,
                "source": "ai_generated_personalized"
            }

        except Exception as e:
            logger.error(f"创建个性化练习失败: {e}")
            return None

    def _build_personalized_system_prompt(self, topic: str, difficulty: str, user_request: str,
                                          user_requirements: Dict[str, Any], weak_dimensions: List[str],
                                          user_level: float) -> str:
        """构建个性化系统提示"""
        prompt = f"""你是一个编程教育专家，负责根据用户的明确要求创建个性化编程练习。

用户明确要求：
- 主题：{topic}
- 难度：{difficulty}
- 具体请求：{user_request}

用户水平：{user_level:.2f}/1.0
重点训练能力：{', '.join(weak_dimensions)}

请严格按照用户要求生成题目，确保：
1. 主题完全匹配用户要求
2. 难度精确符合指定级别
3. 直接回应用户的具体请求"""

        if user_requirements['user_specific_requirements']:
            prompt += f"\n4. 特别关注：{', '.join(user_requirements['user_specific_requirements'])}"

        prompt += "\n\n请按指定格式返回完整题目。"
        return prompt

    def _build_exercise_creation_message(self, topic: str, difficulty: str,
                                         user_requirements: Dict[str, Any],
                                         weak_dimensions: List[str], user_level: float) -> str:
        """构建练习创建消息"""
        return f"""请创建编程练习题目：

主题：{topic}
难度：{difficulty}
用户水平：{user_level:.2f}/1.0
训练重点：{', '.join(weak_dimensions)}

请确保题目：
1. 完全符合指定主题和难度
2. 适合用户当前水平
3. 针对训练重点设计
4. 提供完整描述、要求、示例和提示

格式要求：
标题：[练习标题]
描述：[详细描述]
要求：
1. [要求1]
2. [要求2]
示例：
输入：[示例输入]
输出：[示例输出]
提示：
- [提示1]
- [提示2]
答案：[参考答案]"""

    def _identify_weak_cognitive_dimensions(self, cognitive_state: Dict[str, Any]) -> List[str]:
        """识别薄弱的认知维度"""
        dimensions = cognitive_state.get("cognitive_dimensions", {})
        weak_threshold = 0.6

        weak_dims = []
        for dim, score in dimensions.items():
            if score < weak_threshold:
                weak_dims.append(dim)

        return sorted(weak_dims, key=lambda x: dimensions[x])[:2]

    def _parse_exercise_content(self, content: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """解析生成的练习内容"""
        lines = content.split('\n')
        title = f"{topic}练习"
        description = ""
        requirements = []
        examples = []
        hints = []
        answer = ""

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('标题：'):
                title = line[3:].strip()
            elif line.startswith('描述：'):
                description = line[3:].strip()
                current_section = 'description'
            elif line == '要求：':
                current_section = 'requirements'
            elif line == '示例：':
                current_section = 'examples'
            elif line == '提示：':
                current_section = 'hints'
            elif line == '答案：':
                current_section = 'answer'
            elif current_section == 'requirements' and line.startswith(('1.', '2.', '3.', '-', '•')):
                requirement = line[2:].strip()
                if requirement:
                    requirements.append(requirement)
            elif current_section == 'examples':
                if '输入：' in line:
                    examples.append({"input": line.split('输入：', 1)[-1].strip()})
                elif '输出：' in line and examples:
                    examples[-1]["output"] = line.split('输出：', 1)[-1].strip()
            elif current_section == 'hints' and line.startswith(('-', '•')):
                hint = line[1:].strip()
                if hint:
                    hints.append(hint)
            elif current_section == 'answer':
                answer += line + "\n"

        # 默认值处理
        if not description:
            description = f"请完成关于{topic}的编程练习"
        if not requirements:
            requirements = ["实现指定功能", "处理边界条件", "编写清晰代码"]
        if not examples:
            examples = [{"input": "示例输入", "output": "示例输出"}]
        if not hints:
            hints = ["从简单功能开始", "注意边界条件"]
        if not answer:
            answer = "请根据题目要求实现解决方案"

        return {
            "title": title,
            "description": description,
            "requirements": requirements,
            "difficulty": difficulty,
            "examples": examples,
            "hints": hints,
            "answer": answer.strip()
        }


class EnhancedAnswerProvider:
    """增强版答案提供器 - 优化题目搜索逻辑"""

    def __init__(self):
        self.question_bank_manager = EnhancedQuestionBankManager()
        self.max_search_count = 15  # 最大搜索题目数量限制

    async def provide_contextual_answer(self, user_id: str, content: str,
                                        context: Dict[str, Any] = None) -> Dict[str, Any]:
        """提供基于上下文的答案 - 优化搜索逻辑"""
        try:
            # 确定目标题目
            target_question, search_info = await self._identify_target_question(user_id, content, context)

            if not target_question:
                logger.info(f"未找到匹配题目，直接生成答案。搜索信息: {search_info}")
                return await self._generate_direct_answer(content, context, search_info)

            # 提供答案
            return await self._provide_detailed_answer(target_question, context, search_info)

        except Exception as e:
            logger.error(f"提供答案失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "暂时无法提供答案，请稍后再试。",
                "source": "error"
            }

    async def _identify_target_question(self, user_id: str, content: str,
                                        context: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        识别目标题目，返回题目和搜索信息

        Returns:
            (题目数据, 搜索信息)
        """
        search_info = {
            "searched_count": 0,
            "matched_count": 0,
            "search_strategy": "content_similarity",
            "max_search_reached": False
        }

        try:
            # 1. 检查上下文中的明确引用
            enhanced_context = context.get('enhanced_context', {}) if context else {}
            if enhanced_context.get('exercise_context'):
                search_info["search_strategy"] = "context_reference"
                return enhanced_context['exercise_context'], search_info

            # 2. 从用户输入中提取关键内容用于搜索
            search_content = self._extract_search_content(content)
            if not search_content:
                search_info["search_strategy"] = "no_search_content"
                return None, search_info

            # 3. 在题库中搜索相似题目
            matched_questions, searched_count = self.question_bank_manager.search_questions_by_content(
                search_content, user_id, limit=3, max_search_count=self.max_search_count
            )

            search_info["searched_count"] = searched_count
            search_info["matched_count"] = len(matched_questions)
            search_info["max_search_reached"] = searched_count >= self.max_search_count

            # 4. 选择最佳匹配题目
            if matched_questions:
                # 选择匹配度最高的题目（通常是第一个，因为搜索结果按匹配度排序）
                best_match = matched_questions[0]
                search_info["search_strategy"] = "content_match_found"
                return best_match, search_info

            # 5. 如果搜索了很多题目都没找到，直接返回None
            if searched_count >= self.max_search_count:
                search_info["search_strategy"] = "max_search_exceeded"
                return None, search_info

            # 6. 最后尝试从用户历史中获取最近题目
            user_history = self.question_bank_manager.get_user_question_history(user_id, limit=5)
            if user_history:
                search_info["search_strategy"] = "recent_history"
                search_info["searched_count"] += len(user_history)
                return user_history[0], search_info

            return None, search_info

        except Exception as e:
            logger.error(f"识别目标题目失败: {e}")
            search_info["error"] = str(e)
            return None, search_info

    def _extract_search_content(self, content: str) -> str:
        """从用户输入中提取用于搜索的关键内容"""
        # 移除答案相关的关键词
        answer_keywords = ["答案", "解答", "解一下", "怎么做", "如何实现", "solution", "answer", "help", "请问"]

        cleaned_content = content
        for keyword in answer_keywords:
            cleaned_content = cleaned_content.replace(keyword, "")

        # 移除常见疑问词
        question_words = ["什么", "怎样", "怎么", "如何", "为什么", "能否", "可以", "吗", "呢", "？", "?"]
        for word in question_words:
            cleaned_content = cleaned_content.replace(word, "")

        # 清理文本并返回
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()

        # 如果清理后内容太短，返回原始内容（去除首尾空格）
        if len(cleaned_content) < 10:
            return content.strip()

        return cleaned_content

    async def _provide_detailed_answer(self, target_question: Dict[str, Any],
                                       context: Dict[str, Any],
                                       search_info: Dict[str, Any]) -> Dict[str, Any]:
        """提供详细答案"""
        try:
            # 提取题目描述
            question_text = self._extract_question_text(target_question)

            # 如果有现成答案，直接使用
            if self._has_complete_answer(target_question):
                return {
                    "success": True,
                    "answer": self._get_complete_answer(target_question),
                    "source": "question_bank",
                    "personalized": True,
                    "question_preview": question_text[:100] + "...",
                    "search_info": search_info
                }

            # 使用LLM生成答案
            return await self._generate_llm_answer(question_text, target_question, search_info)

        except Exception as e:
            logger.error(f"提供详细答案失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": "error",
                "search_info": search_info
            }

    async def _generate_direct_answer(self, content: str, context: Dict[str, Any],
                                      search_info: Dict[str, Any]) -> Dict[str, Any]:
        """直接根据用户输入生成答案（当找不到匹配题目时）"""
        try:
            # 从用户输入中提取题目描述
            question_text = self._extract_question_from_request(content)

            system_prompt = """你是一个编程教育专家，擅长根据不完整的题目描述提供准确的解答和解析。"""

            user_message = f"""用户请求解答以下编程题目，但题目描述可能不完整：

题目描述：
{question_text}

请根据你的专业知识：
1. 推测完整的题目要求
2. 提供完整的代码解决方案
3. 给出详细的解题思路和解释
4. 提供关键知识点的说明

请确保答案准确、清晰、易于理解。"""

            answer = await llm_client.generate_response(system_prompt, user_message)

            return {
                "success": True,
                "answer": answer,
                "source": "llm_generated_direct",
                "personalized": False,
                "question_preview": question_text[:100] + "...",
                "search_info": search_info,
                "note": "根据您的描述直接生成答案"
            }

        except Exception as e:
            logger.error(f"直接生成答案失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "无法生成答案，请提供更详细的题目描述。",
                "source": "error",
                "search_info": search_info
            }

    def _extract_question_from_request(self, content: str) -> str:
        """从用户请求中提取题目描述"""
        # 移除答案请求相关的词语
        answer_phrases = [
            "这道题的答案", "这个题目的解答", "请解答", "求答案", "帮忙解答",
            "解答一下", "怎么做这道题", "如何实现这个功能"
        ]

        question_text = content
        for phrase in answer_phrases:
            question_text = question_text.replace(phrase, "")

        return question_text.strip()

    def _has_complete_answer(self, question_data: Dict[str, Any]) -> bool:
        """检查题目是否有完整答案"""
        if question_data.get('content', {}).get('answer'):
            answer = question_data['content']['answer']
            return len(str(answer).strip()) > 10  # 答案不能太短

        # 检查直接包含的answer字段
        if question_data.get('answer'):
            answer = question_data['answer']
            return len(str(answer).strip()) > 10

        return False

    def _get_complete_answer(self, question_data: Dict[str, Any]) -> str:
        """获取完整答案"""
        if question_data.get('content', {}).get('answer'):
            return question_data['content']['answer']

        if question_data.get('answer'):
            return question_data['answer']

        return ""

    def _extract_question_text(self, question_data: Dict[str, Any]) -> str:
        """提取题目文本"""
        if isinstance(question_data, dict):
            if 'description' in question_data:
                return question_data['description']
            elif 'content' in question_data and isinstance(question_data['content'], dict):
                content = question_data['content']
                description = content.get('description', '')
                title = content.get('title', '')
                requirements = "\n".join(content.get('requirements', []))
                return f"{title}\n{description}\n{requirements}"
        return str(question_data)

    async def _generate_llm_answer(self, question_text: str,
                                   target_question: Dict[str, Any],
                                   search_info: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM生成答案"""
        system_prompt = """你是一个编程教育专家，擅长提供详细的题目解答和解析。"""

        user_message = f"""请为以下编程题目提供详细的答案和解析：

题目：
{question_text}

请提供：
1. 完整的代码解决方案
2. 逐步的解题思路
3. 关键知识点的解释
4. 可能的变种或扩展
5. 常见错误和避免方法

请确保答案清晰、准确、易于理解。"""

        answer = await llm_client.generate_response(system_prompt, user_message)

        return {
            "success": True,
            "answer": answer,
            "source": "llm_generated",
            "personalized": False,
            "question_preview": question_text[:100] + "...",
            "search_info": search_info
        }


class EnhancedExerciseGenerationAgent(BaseAgent):
    """增强版练习生成代理"""

    def __init__(self, personal_agent):
        super().__init__("EnhancedExerciseGenerationAgent")
        self.exercise_generator = EnhancedExerciseGenerator()
        self.answer_provider = EnhancedAnswerProvider()  # 使用优化后的答案提供器
        self.personal_agent = personal_agent
        self.cognition_api = get_scientific_cognitive_api_sync()
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理练习生成请求"""
        user_id = request["user_id"]
        content = request["content"]
        context = request.get("context", {})

        self.log_activity("处理增强版练习请求", {
            "user_id": user_id,
            "content": content[:100],
            "has_context": bool(context)
        })

        # 检查请求类型
        if self._is_answer_request(content):
            return await self._handle_enhanced_answer_request(user_id, content, context)
        elif self._is_quiz_request(content):
            return await self._handle_quiz_request(user_id, content, context)
        else:
            return await self._handle_exercise_request(user_id, content, context)

    async def _handle_enhanced_answer_request(self, user_id: str, content: str,
                                              context: Dict[str, Any]) -> Dict[str, Any]:
        """处理增强版答案请求 - 使用优化后的答案提供器"""
        try:
            answer_result = await self.answer_provider.provide_contextual_answer(
                user_id, content, context
            )

            # 构建响应消息
            if answer_result.get("success", False):
                response = self._build_answer_response(answer_result, content)
            else:
                response = f"❌ {answer_result.get('error', '无法提供答案')}"

            return {
                "response": response,
                "details": {
                    "answer_provided": answer_result.get("success", False),
                    "source": answer_result.get("source", "unknown"),
                    "personalized": answer_result.get("personalized", False),
                    "search_info": answer_result.get("search_info", {})
                },
                "success": answer_result.get("success", False)
            }

        except Exception as e:
            logger.error(f"处理答案请求失败: {e}")
            return {
                "response": "处理答案请求时出现错误，请稍后再试。",
                "success": False
            }

    def _build_answer_response(self, answer_result: Dict[str, Any], user_request: str) -> str:
        """构建答案响应消息"""
        source_info = {
            "question_bank": "📚 来自题库答案",
            "llm_generated": "🤖 AI生成的解答",
            "llm_generated_direct": "🤖 根据描述生成的解答",
            "error": "❌ 生成失败"
        }

        source = answer_result.get("source", "unknown")
        source_text = source_info.get(source, "🔍 生成的解答")

        response = f"{source_text}\n\n"
        response += f"{answer_result['answer']}"

        # 添加搜索信息说明
        search_info = answer_result.get("search_info", {})
        if search_info.get("max_search_reached"):
            response += f"\n\n💡 提示：已搜索{search_info.get('searched_count', 0)}个题目，未找到完全匹配的，当前解答基于题目描述生成。"
        elif search_info.get("searched_count", 0) > 0:
            response += f"\n\n💡 提示：已匹配题库中的相关题目。"

        return response

    async def _handle_quiz_request(self, user_id: str, content: str,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """处理测验请求"""
        # 使用增强版生成器处理测验
        result = await self.exercise_generator.generate_exercise_with_priority(
            user_id, content, context
        )
        return await self._build_exercise_response(result, "测验")

    async def _handle_exercise_request(self, user_id: str, content: str,
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """处理练习请求"""
        result = await self.exercise_generator.generate_exercise_with_priority(
            user_id, content, context
        )
        return await self._build_exercise_response(result, "练习")

    async def _build_exercise_response(self, result: Dict[str, Any], exercise_type: str) -> Dict[str, Any]:
        """构建练习响应"""
        if result.get("success", False):
            response_msg = self._build_success_message(result, exercise_type)
            exercises_text = self._format_exercises_for_display(result)
            full_response = response_msg + "\n\n" + exercises_text
        else:
            full_response = f"生成{exercise_type}失败: {result.get('error', '未知错误')}"

        return {
            "response": full_response,
            "details": self._build_response_details(result),
            "success": result.get("success", False)
        }

    def _build_success_message(self, result: Dict[str, Any], exercise_type: str) -> str:
        """构建成功消息"""
        base_msg = f"✅ 已生成{exercise_type}"

        # 添加题目数量信息
        question_count = self._count_questions(result)
        if question_count > 1:
            base_msg += f"，共{question_count}道题目"

        # 添加个性化信息
        if result.get("personalized", False):
            base_msg += " (个性化推荐)"

        # 添加用户要求满足信息
        if result.get("user_requirements_met", False):
            base_msg += " (符合您的要求)"

        return base_msg

    def _count_questions(self, result: Dict[str, Any]) -> int:
        """计算题目数量"""
        if "questions" in result:
            return len(result["questions"])
        elif "exercise" in result:
            return 1
        return 0

    def _format_exercises_for_display(self, result: Dict[str, Any]) -> str:
        """格式化练习题目用于显示"""
        exercises_text = "📋 练习题目：\n\n"

        if "questions" in result:
            for i, question in enumerate(result["questions"], 1):
                exercises_text += self._format_single_exercise(question, i)
                if i < len(result["questions"]):
                    exercises_text += "\n" + "=" * 50 + "\n\n"
        elif "exercise" in result:
            exercises_text += self._format_single_exercise(result["exercise"], 1)

        # 添加来源信息
        source_info = {
            "question_bank": "📚 来自题库",
            "ai_generated": "🤖 AI生成",
            "mixed": "🔄 混合来源"
        }

        source = result.get("source", "unknown")
        if source in source_info:
            exercises_text += f"\n\n{source_info[source]}"

        return exercises_text

    def _format_single_exercise(self, exercise_data: Dict[str, Any], index: int) -> str:
        """格式化单个练习题目"""
        content = exercise_data.get("content", {})

        text = f"🔹 题目 {index}: {content.get('title', '未命名题目')}\n"
        text += f"📝 描述: {content.get('description', '')}\n\n"

        text += "📋 要求:\n"
        for req in content.get('requirements', []):
            text += f"  • {req}\n"

        text += "\n💡 示例:\n"
        for example in content.get('examples', []):
            text += f"  输入: {example.get('input', '')}\n"
            text += f"  输出: {example.get('output', '')}\n"

        text += "\n💡 提示:\n"
        for hint in content.get('hints', []):
            text += f"  • {hint}\n"

        text += f"\n🎯 难度: {exercise_data.get('difficulty', '未知')}"
        text += f" | 主题: {exercise_data.get('topic', '通用')}"

        return text

    def _build_response_details(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """构建响应详情"""
        details = {
            "type": result.get("type", "unknown"),
            "topic": result.get("topic", "general"),
            "difficulty": result.get("difficulty", "intermediate"),
            "personalized": result.get("personalized", False),
            "source": result.get("source", "unknown"),
            "user_requirements_met": result.get("user_requirements_met", False)
        }

        # 添加题目信息
        if "questions" in result:
            details["question_count"] = len(result["questions"])
            details["questions"] = result["questions"]
        elif "exercise" in result:
            details["question_count"] = 1
            details["exercise"] = result["exercise"]

        # 添加需求分析信息
        if "requirements_analysis" in result:
            details["requirements_analysis"] = result["requirements_analysis"]

        return details

    def _is_answer_request(self, content: str) -> bool:
        """判断是否是答案请求"""
        answer_keywords = ["答案", "解答", "解一下", "怎么做", "如何实现", "solution", "answer", "help"]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in answer_keywords)

    def _is_quiz_request(self, content: str) -> bool:
        """判断是否是测验请求"""
        quiz_keywords = ["测验", "测试", "quiz", "exam", "考试"]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in quiz_keywords)

    async def _record_cognitive_data(self, user_id: str, content: str, result: Dict[str, Any]):
        """记录科学认知数据"""
        try:
            interaction_data = {
                'type': 'exercise_generation',
                'content': content[:500],
                'user_response': str(result.get('type', 'unknown')),
                'context': '练习生成交互',
                'metadata': {
                    'exercise_type': result.get('type', 'unknown'),
                    'success': result.get('success', False),
                    'personalized': result.get('personalized', False),
                    'user_requirements_met': result.get('user_requirements_met', False)
                }
            }

            analysis_result = await self.cognition_api.analyze_learning_interaction(user_id, interaction_data)

            if analysis_result['success']:
                logger.info("练习生成认知分析完成")

        except Exception as e:
            logger.warning(f"记录认知数据失败: {e}")