# src/programming_education_system/agents/exercise_agent.py
"""
练习生成代理 - 与题库集成版本
支持智能题库管理、上下文感知、避免重复题目
"""
from typing import Dict, Any, List, Optional
import logging
import asyncio
import json
import time
import hashlib
from datetime import datetime

from programming_education_system.models.question_bank import QuestionBank, DifficultyLevel, QuestionType
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

# 导入科学认知API
from programming_education_system.cognition_judger.cognitive_api_scientific import get_scientific_cognitive_api, \
    get_scientific_cognitive_api_sync

logger = logging.getLogger(__name__)


class SmartQuestionBankManager:
    """智能题库管理器 - 与数据库题库集成"""

    def __init__(self):
        self.question_bank = QuestionBank()
        self.generated_questions_cache = {}  # 用户ID -> 已生成题目哈希集合
        self.cognition_api = get_scientific_cognitive_api_sync()

        # 初始化一些示例题目（如果题库为空）
        self._initialize_sample_questions()

    def _initialize_sample_questions(self):
        """如果题库为空，初始化一些示例题目"""
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
                "topic": "data_structures",
                "content": "编写一个函数，反转列表中的元素。",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "question_type": QuestionType.CODING,
                "answer": "def reverse_list(lst):\n    return lst[::-1]",
                "hints": ["使用切片操作", "也可以使用reversed()函数"],
                "examples": [
                    {"input": "reverse_list([1, 2, 3])", "output": "[3, 2, 1]"},
                    {"input": "reverse_list(['a', 'b', 'c'])", "output": "['c', 'b', 'a']"}
                ],
                "tags": ["列表", "算法"],
                "source": "system"
            }
        ]

        for question_data in sample_questions:
            self.question_bank.add_question(**question_data)

    def _generate_question_hash(self, question_content: Dict[str, Any]) -> str:
        """生成题目内容的哈希值，用于去重"""
        # 使用描述和要求作为哈希基础
        content_str = f"{question_content.get('description', '')}{''.join(question_content.get('requirements', []))}"
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()

    async def find_matching_questions(self, user_id: str, topic: str = None,
                                      difficulty: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """在题库中查找匹配的题目"""
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
                limit=limit
            )

            # 获取用户已见过的题目哈希
            seen_hashes = self.generated_questions_cache.get(user_id, set())

            # 转换格式并过滤已见过的题目
            result_questions = []
            for q in questions:
                # 创建题目哈希
                question_content = {
                    "description": q.content,
                    "requirements": ["完成题目要求"]  # 默认要求
                }
                question_hash = self._generate_question_hash(question_content)

                if question_hash not in seen_hashes:
                    # 转换题库题目为代理期望的格式
                    result_questions.append({
                        "id": q.id,
                        "type": q.question_type.value,
                        "topic": q.topic,
                        "difficulty": q.difficulty.value,
                        "content": {
                            "title": f"题库题目 - {q.topic}",
                            "description": q.content,
                            "requirements": ["完成题目要求"],
                            "difficulty": q.difficulty.value,
                            "examples": q.examples or [{"input": "示例输入", "output": "示例输出"}],
                            "hints": q.hints or ["从简单功能开始", "注意边界条件"],
                            "answer": q.answer or "参考答案待提供"
                        },
                        "source": "question_bank",
                        "hash": question_hash
                    })

            return result_questions

        except Exception as e:
            logger.error(f"查找匹配题目失败: {e}")
            return []

    async def save_generated_question(self, user_id: str, question_data: Dict[str, Any]) -> str:
        """保存生成的题目到题库"""
        try:
            content = question_data['content']

            # 生成题目哈希
            question_hash = self._generate_question_hash(content)

            # 检查是否已存在
            if question_hash in self.generated_questions_cache.get(user_id, set()):
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

            # 更新缓存
            if user_id not in self.generated_questions_cache:
                self.generated_questions_cache[user_id] = set()
            self.generated_questions_cache[user_id].add(question_hash)

            logger.info(f"已保存生成题目到题库: {question_id}, 用户: {user_id}")
            return question_hash

        except Exception as e:
            logger.error(f"保存生成题目失败: {e}")
            return ""

    def get_user_question_history(self, user_id: str) -> List[str]:
        """获取用户已见过的题目哈希列表"""
        return list(self.generated_questions_cache.get(user_id, set()))

    def update_question_usage(self, question_id: int, success: bool = True):
        """更新题目使用统计"""
        try:
            self.question_bank.update_question_usage(question_id, success)
        except Exception as e:
            logger.error(f"更新题目使用统计失败: {e}")


class ContextAwareExerciseGenerator:
    """上下文感知的练习生成器"""

    def __init__(self):
        self.cognition_api = get_scientific_cognitive_api_sync()
        self.question_bank_manager = SmartQuestionBankManager()

    async def generate_exercise_with_context(self, user_id: str, user_request: str,
                                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """基于上下文生成练习"""

        # 解析用户需求
        parsed_request = self._parse_user_request(user_request, context)
        topic = parsed_request.get('topic')
        explicit_difficulty = parsed_request.get('difficulty')
        exercise_type = parsed_request.get('type', 'preset')

        # 获取用户认知状态
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        user_level = cognitive_state["overall_cognitive_level"]

        # 确定难度：优先用户明确要求，其次基于认知水平
        if explicit_difficulty:
            difficulty = explicit_difficulty
        else:
            if user_level < 0.4:
                difficulty = "beginner"
            elif user_level < 0.7:
                difficulty = "intermediate"
            else:
                difficulty = "advanced"

        # 首先尝试从题库查找匹配题目（除非用户明确要求新题目）
        if exercise_type != "new":
            library_questions = await self.question_bank_manager.find_matching_questions(
                user_id, topic, difficulty, limit=3
            )

            if library_questions:
                # 使用题库中的题目
                return {
                    "success": True,
                    "type": "preset",
                    "questions": library_questions,
                    "source": "question_bank",
                    "personalized": True,
                    "context_used": True
                }

        # 生成新题目
        return await self._generate_new_exercise(user_id, topic, difficulty,
                                                 cognitive_state, user_request)

    def _parse_user_request(self, user_request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析用户请求，结合上下文"""
        request_lower = user_request.lower()
        parsed = {
            'topic': None,
            'difficulty': None,
            'type': 'preset'
        }

        # 从上下文获取信息
        if context:
            recent_history = context.get('recent_history', [])
            if recent_history:
                # 分析最近对话主题
                last_topic = recent_history[0].get('topic', 'general')
                parsed['topic'] = last_topic

        # 解析主题关键词
        topic_keywords = {
            "python_basics": ["python", "基础", "语法", "变量", "函数", "入门", "基础"],
            "data_structures": ["数据结构", "列表", "字典", "元组", "集合", "数组", "链表"],
            "algorithms": ["算法", "排序", "查找", "递归", "复杂度", "二分", "动态规划"],
            "oop": ["面向对象", "类", "对象", "继承", "多态", "封装", "oop"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                parsed['topic'] = topic
                break

        # 解析难度关键词
        if any(word in request_lower for word in ["简单", "基础", "入门", "beginner", "easy"]):
            parsed['difficulty'] = "beginner"
        elif any(word in request_lower for word in ["难", "高级", "复杂", "advanced", "hard"]):
            parsed['difficulty'] = "advanced"
        elif any(word in request_lower for word in ["中等", "普通", "intermediate", "medium"]):
            parsed['difficulty'] = "intermediate"

        # 解析练习类型
        if any(word in request_lower for word in ["新", "重新", "换一个", "另一个", "new", "another"]):
            parsed['type'] = "new"
        elif any(word in request_lower for word in ["测验", "测试", "quiz", "exam"]):
            parsed['type'] = "quiz"

        return parsed

    async def _generate_new_exercise(self, user_id: str, topic: str, difficulty: str,
                                     cognitive_state: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """生成新练习题目"""
        try:
            # 获取学习推荐和个性化参数
            learning_recs = await self.cognition_api.get_learning_recommendations(user_id, topic)
            learning_params = await self.cognition_api.get_personalized_learning_parameters(user_id, "practice")

            # 识别认知薄弱维度
            weak_dimensions = self._identify_weak_cognitive_dimensions(cognitive_state)

            # 生成练习内容
            exercise = await self._create_contextual_exercise(
                topic, difficulty, weak_dimensions, learning_params,
                cognitive_state["overall_cognitive_level"], user_request
            )

            # 保存到题库
            question_hash = await self.question_bank_manager.save_generated_question(user_id, exercise)

            return {
                "success": True,
                "type": "generated",
                "exercise": exercise,
                "source": "ai_generated",
                "personalized": True,
                "saved_to_library": bool(question_hash),
                "cognitive_basis": {
                    "user_level": cognitive_state["overall_cognitive_level"],
                    "weak_dimensions": weak_dimensions,
                    "learning_parameters": learning_params
                }
            }

        except Exception as e:
            logger.error(f"生成新练习失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "exercise": self._get_fallback_exercise(topic, difficulty)
            }

    async def _create_contextual_exercise(self, topic: str, difficulty: str,
                                          weak_dimensions: List[str],
                                          learning_params: Dict[str, Any],
                                          user_level: float,
                                          user_request: str) -> Dict[str, Any]:
        """创建基于上下文的练习题目"""

        # 基于薄弱认知维度设计练习重点
        dimension_focus = self._map_dimensions_to_exercise_focus(weak_dimensions)

        system_prompt = """你是一个编程教育专家，擅长设计针对特定认知维度训练的编程练习。请根据用户的具体需求生成合适的编程练习题目。

用户需求：{user_request}
学习主题：{topic}
难度级别：{difficulty}  
用户认知水平：{user_level}
认知训练重点：{dimension_focus}

请设计一个能够满足用户需求并有效训练目标认知维度的编程练习题目。"""

        user_message = """请根据以下信息生成编程练习：

用户具体请求：{user_request}
主题：{topic}
难度：{difficulty}
用户水平：{user_level:.2f}/1.0
重点训练能力：{dimension_focus}

请确保题目：
1. 直接回应用户的具体需求
2. 难度适合指定水平
3. 针对目标认知维度进行训练
4. 提供清晰的描述、要求和示例

请按以下格式返回：

标题：[练习标题]
描述：[详细的题目描述]
要求：
1. [具体要求1]
2. [具体要求2]
3. [具体要求3]

示例：
输入：[示例输入]
输出：[示例输出]

提示：
- [提示1]
- [提示2]

答案：
[标准答案或解题思路]

难度：{difficulty}
主题：{topic}""".format(
            user_request=user_request,
            topic=topic or '编程基础',
            difficulty=difficulty,
            user_level=user_level,
            dimension_focus=', '.join(dimension_focus)
        )

        generated_content = await llm_client.generate_response(system_prompt, user_message)

        # 解析生成的练习内容
        exercise_data = self._parse_exercise_content(generated_content, topic, difficulty)

        return {
            "type": "contextual_training",
            "topic": topic or "general",
            "difficulty": difficulty,
            "content": exercise_data,
            "cognitive_focus": weak_dimensions,
            "user_request": user_request,
            "source": "context_aware_generated"
        }

    def _identify_weak_cognitive_dimensions(self, cognitive_state: Dict[str, Any]) -> List[str]:
        """识别薄弱的认知维度"""
        dimensions = cognitive_state.get("cognitive_dimensions", {})
        weak_threshold = 0.6

        weak_dims = []
        for dim, score in dimensions.items():
            if score < weak_threshold:
                weak_dims.append(dim)

        return sorted(weak_dims, key=lambda x: dimensions[x])[:2]

    def _map_dimensions_to_exercise_focus(self, dimensions: List[str]) -> List[str]:
        """将认知维度映射到练习重点"""
        dimension_mapping = {
            'remember': '概念记忆和语法掌握',
            'understand': '原理理解和概念解释',
            'apply': '实际应用和代码实现',
            'analyze': '代码分析和问题分解',
            'evaluate': '代码评审和质量评估',
            'create': '创新设计和解决方案构建'
        }
        return [dimension_mapping.get(dim, '综合能力') for dim in dimensions]

    def _parse_exercise_content(self, content: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """解析生成的练习内容（增强版，包含答案解析）"""
        lines = content.split('\n')
        title = f"{topic or '编程'}练习"
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
            elif line.startswith('难度：') or line.startswith('主题：'):
                current_section = None
            elif current_section == 'requirements' and line.startswith(('1.', '2.', '3.', '-', '•')):
                requirement = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip() if line.startswith(
                    ('-', '•')) else line
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
            elif current_section == 'description' and not line.startswith(('要求：', '示例：', '提示：', '答案：')):
                description += " " + line

        # 默认值处理
        if not description:
            description = content[:500]
        if not requirements:
            requirements = ["完成指定功能", "处理边界条件", "编写清晰的代码"]
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

    def _get_fallback_exercise(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """获取回退练习"""
        return {
            "type": "fallback",
            "topic": topic or "general",
            "difficulty": difficulty or "intermediate",
            "content": {
                "title": f"{topic or '编程'}基础练习",
                "description": f"请完成一个关于{topic}的练习：实现一个简单的功能函数。",
                "requirements": [
                    "实现指定功能",
                    "处理边界条件",
                    "编写清晰的代码"
                ],
                "difficulty": difficulty or "intermediate",
                "examples": [
                    {"input": "示例输入", "output": "示例输出"}
                ],
                "hints": ["从简单功能开始", "注意边界条件"],
                "answer": "标准解决方案"
            },
            "cognitive_focus": ["apply"],
            "source": "fallback"
        }


class AnswerProvider:
    """答案提供器"""

    def __init__(self):
        self.question_bank_manager = SmartQuestionBankManager()

    async def provide_answer(self, user_id: str, question_content: str, context: Dict[str, Any] = None) -> Dict[
        str, Any]:
        """提供题目答案和解析"""
        try:
            # 首先尝试从题库搜索匹配的题目
            matching_questions = await self.question_bank_manager.find_matching_questions(
                user_id, limit=5
            )

            # 简单的关键词匹配（在实际应用中可以使用更复杂的相似度匹配）
            for question in matching_questions:
                if any(keyword in question['content']['description'] for keyword in question_content.split()[:3]):
                    if question['content'].get('answer'):
                        return {
                            "success": True,
                            "answer": question['content']['answer'],
                            "source": "question_bank",
                            "personalized": True
                        }

            # 使用LLM生成答案
            return await self._generate_answer_with_llm(question_content, context)

        except Exception as e:
            logger.error(f"提供答案失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "暂时无法提供答案，请稍后再试。"
            }

    async def _generate_answer_with_llm(self, question_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM生成答案和解析"""
        system_prompt = """你是一个编程教育专家，擅长提供详细的题目解答和解析。请为以下编程题目提供完整的答案和解析。"""

        user_message = f"""请为以下编程题目提供详细的答案和解析：

题目：
{question_content}

请提供：
1. 完整的代码解决方案
2. 逐步的解题思路
3. 关键知识点的解释
4. 可能的变种或扩展

请确保答案清晰、准确、易于理解。"""

        answer = await llm_client.generate_response(system_prompt, user_message)

        return {
            "success": True,
            "answer": answer,
            "source": "llm_generated",
            "personalized": False
        }


class QuizGenerator:
    """测验生成器 - 与题库集成"""

    def __init__(self):
        self.cognition_api = get_scientific_cognitive_api_sync()
        self.question_bank_manager = SmartQuestionBankManager()

    async def generate_adaptive_quiz(self, user_id: str, topic: str = None) -> Dict[str, Any]:
        """生成自适应测验"""
        try:
            # 获取用户认知状态
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
            user_level = cognitive_state["overall_cognitive_level"]

            # 根据认知水平确定难度和题目数量
            if user_level < 0.4:
                difficulty = "beginner"
                question_count = 3
            elif user_level < 0.7:
                difficulty = "intermediate"
                question_count = 5
            else:
                difficulty = "advanced"
                question_count = 7

            # 从题库获取题目
            questions = await self.question_bank_manager.find_matching_questions(
                user_id, topic, difficulty, question_count
            )

            # 如果题库题目不足，补充一些
            if len(questions) < question_count:
                needed = question_count - len(questions)
                logger.info(f"题库题目不足，需要补充{needed}道题目")
                # 这里可以调用生成器生成额外题目

            return {
                "success": True,
                "type": "quiz",
                "topic": topic or "general",
                "difficulty": difficulty,
                "question_count": len(questions),
                "questions": questions,
                "adaptive": True
            }

        except Exception as e:
            logger.error("生成自适应测验失败: {}".format(e))
            # 返回基础测验
            questions = await self.question_bank_manager.find_matching_questions(user_id, topic, limit=3)
            return {
                "success": False,
                "type": "quiz",
                "topic": topic or "general",
                "difficulty": "intermediate",
                "question_count": len(questions),
                "questions": questions,
                "adaptive": False
            }


class ExerciseGenerationAgent(BaseAgent):
    """练习生成代理 - 与题库集成版本"""

    def __init__(self, personal_agent):
        super().__init__("ExerciseGenerationAgent")
        self.context_aware_generator = ContextAwareExerciseGenerator()
        self.answer_provider = AnswerProvider()
        self.quiz_generator = QuizGenerator()
        self.personal_agent = personal_agent
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理练习生成请求 - 集成题库版本"""
        user_id = request["user_id"]
        content = request["content"]
        context = request.get("context", {})

        self.log_activity("处理练习请求", {
            "user_id": user_id,
            "content_preview": content[:50] + "...",
            "has_context": bool(context)
        })

        # 检查是否是请求答案
        if self._is_answer_request(content):
            return await self._handle_answer_request(user_id, content, context)

        # 检查是否是测验请求
        if self._is_quiz_request(content):
            topic = self._parse_topic(content)
            result = await self.quiz_generator.generate_adaptive_quiz(user_id, topic)
        else:
            # 生成普通练习
            result = await self.context_aware_generator.generate_exercise_with_context(
                user_id, content, context
            )

        # 记录科学认知数据
        await self._record_cognitive_data(user_id, content, result)

        # 记录用户行为
        behavior_data = {
            "user_id": user_id,
            "exercise_type": result.get("type", "unknown"),
            "topic": result.get("topic", "general"),
            "success": result.get("success", False),
            "personalized": result.get("personalized", False),
            "source": result.get("source", "unknown"),
            "question_count": self._count_questions(result)
        }
        await self.personal_agent.track_user_behavior(behavior_data)

        # 构建响应
        if result.get("success", False):
            response_msg = self._build_success_response(result)
            full_response = response_msg + "\n\n" + self._format_exercises_for_display(result)
        else:
            response_msg = f"生成练习失败: {result.get('error', '未知错误')}"
            full_response = response_msg

        return {
            "response": full_response,
            "details": self._build_response_details(result),
            "success": result.get("success", False)
        }

    async def _handle_answer_request(self, user_id: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理答案请求 - 强化上下文处理"""
        try:
            # 从上下文中提取题目内容
            question_content = self._extract_question_from_context(content, context)

            if not question_content:
                # 如果没有明确的题目，提供友好的提示
                last_exercise_topic = context.get('conversation_context', {}).get('last_exercise_topic')
                if last_exercise_topic:
                    return {
                        "response": f"请提供需要解答的具体题目内容。您最近在练习{last_exercise_topic}相关的题目，请告诉我您需要解答哪个具体题目？",
                        "success": False
                    }
                else:
                    return {
                        "response": "请提供需要解答的具体题目内容，或者先生成一个练习题目。",
                        "success": False
                    }

            # 提供答案
            answer_result = await self.answer_provider.provide_answer(user_id, question_content, context)

            if answer_result.get("success", False):
                response = f"🔍 题目解答：\n\n{answer_result['answer']}"
            else:
                response = f"暂时无法提供答案：{answer_result.get('error', '未知错误')}"

            return {
                "response": response,
                "details": {
                    "answer_provided": answer_result.get("success", False),
                    "source": answer_result.get("source", "unknown"),
                    "question_topic": context.get('conversation_context', {}).get('last_exercise_topic', 'unknown')
                },
                "success": answer_result.get("success", False)
            }

        except Exception as e:
            logger.error(f"处理答案请求失败: {e}")
            return {
                "response": "处理答案请求时出现错误，请稍后再试。",
                "success": False
            }

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

    def _extract_question_from_context(self, content: str, context: Dict[str, Any]) -> str:
        """从上下文中提取题目内容 - 强化版"""
        # 1. 首先检查用户当前输入是否包含题目
        if len(content.strip()) > 30:  # 如果输入较长，可能直接包含题目
            return content

        # 2. 检查最近对话历史中的题目
        recent_history = context.get('recent_history', [])
        for history in recent_history[:3]:
            agent_response = history.get('agent_response', '')

            # 从助手回复中提取题目描述
            lines = agent_response.split('\n')
            for line in lines:
                if "描述:" in line:
                    description = line.replace("描述:", "").strip()
                    if description:
                        return description
                elif "题目" in line and ":" in line:
                    question = line.split(":", 1)[1].strip()
                    if question:
                        return question

        # 3. 检查上下文中的练习预览信息
        conversation_context = context.get('conversation_context', {})
        if 'last_question_preview' in conversation_context:
            return conversation_context['last_question_preview']

        # 4. 如果都没有，返回空字符串
        return ""

    def _parse_topic(self, content: str) -> str:
        """解析主题"""
        content_lower = content.lower()

        topic_keywords = {
            "python_basics": ["python", "基础", "语法", "变量", "函数", "入门"],
            "data_structures": ["数据结构", "列表", "字典", "元组", "集合", "数组"],
            "algorithms": ["算法", "排序", "查找", "递归", "复杂度", "二分"],
            "oop": ["面向对象", "类", "对象", "继承", "多态", "封装"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return topic

        return None

    def _format_exercises_for_display(self, result: Dict[str, Any]) -> str:
        """格式化练习题目用于显示"""
        exercises_text = "📋 练习题目：\n\n"

        if "questions" in result:
            # 多个题目的情况
            for i, question in enumerate(result["questions"], 1):
                exercises_text += self._format_single_exercise(question, i)
                if i < len(result["questions"]):
                    exercises_text += "\n" + "=" * 50 + "\n\n"
        elif "exercise" in result:
            # 单个练习的情况
            exercises_text += self._format_single_exercise(result["exercise"], 1)

        # 添加来源信息
        source_info = {
            "question_bank": "📚 来自题库",
            "ai_generated": "🤖 AI生成",
            "context_aware_generated": "🎯 基于上下文生成"
        }

        source = result.get("source", "unknown")
        if source in source_info:
            exercises_text += f"\n\n{source_info[source]}"
            if result.get("saved_to_library", False):
                exercises_text += " (已保存到题库)"

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

    def _count_questions(self, result: Dict[str, Any]) -> int:
        """计算题目数量"""
        if "questions" in result:
            return len(result["questions"])
        elif "exercise" in result:
            return 1
        return 0

    def _build_response_details(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """构建响应详情"""
        details = {
            "type": result.get("type", "unknown"),
            "topic": result.get("topic", "general"),
            "difficulty": result.get("difficulty", "intermediate"),
            "personalized": result.get("personalized", False),
            "source": result.get("source", "unknown"),
            "context_used": result.get("context_used", False)
        }

        # 添加题目信息
        if "questions" in result:
            details["question_count"] = len(result["questions"])
            details["questions"] = result["questions"]
        elif "exercise" in result:
            details["question_count"] = 1
            details["exercise"] = result["exercise"]

        # 添加认知基础信息
        if "cognitive_basis" in result:
            details["cognitive_basis"] = result["cognitive_basis"]

        return details

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
                    'topic': result.get('topic', 'general'),
                    'source': result.get('source', 'unknown'),
                    'question_count': self._count_questions(result)
                }
            }

            analysis_result = await self.cognition_api.analyze_learning_interaction(user_id, interaction_data)

            if analysis_result['success']:
                self.logger.info("练习生成认知分析完成")

        except Exception as e:
            self.logger.warning(f"记录认知数据失败: {e}")

    def _build_success_response(self, result: Dict[str, Any]) -> str:
        """构建成功响应消息"""
        type_names = {
            "preset": "题库练习",
            "generated": "个性化练习",
            "contextual_training": "上下文感知练习",
            "quiz": "自适应测验"
        }

        base_msg = "✅ 已生成{}".format(type_names.get(result.get("type", "unknown"), "练习"))

        # 添加题目数量信息
        question_count = self._count_questions(result)
        if question_count > 1:
            base_msg += f"，共{question_count}道题目"

        # 添加个性化信息
        if result.get("personalized", False):
            base_msg += " (个性化推荐)"

        if result.get("context_used", False):
            base_msg += " (基于上下文)"

        return base_msg