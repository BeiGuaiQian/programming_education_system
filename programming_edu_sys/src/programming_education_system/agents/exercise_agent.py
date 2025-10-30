# src/programming_education_system/agents/exercise_agent.py
"""
练习生成代理 - 科学认知API版本
基于用户认知状态生成个性化编程练习
"""
from typing import Dict, Any, List, Optional
import logging
import asyncio
import json
import time

from programming_education_system.models.question_bank import QuestionBank, DifficultyLevel, QuestionType
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

# 导入科学认知API
from programming_education_system.cognition_judger.cognitive_api_scientific import get_scientific_cognitive_api, \
    get_scientific_cognitive_api_sync

logger = logging.getLogger(__name__)


class CognitiveExerciseGenerator:
    """基于认知科学的练习生成器"""

    def __init__(self):
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def generate_cognitive_exercise(self, user_id: str, topic: str = None) -> Dict[str, Any]:
        """基于用户认知状态生成个性化练习"""

        try:
            # 获取用户认知状态
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)

            # 获取学习推荐
            learning_recs = await self.cognition_api.get_learning_recommendations(user_id, topic)

            # 获取个性化参数
            learning_params = await self.cognition_api.get_personalized_learning_parameters(user_id, "practice")

            # 基于认知水平确定难度
            overall_level = cognitive_state["overall_cognitive_level"]
            recommended_difficulty = learning_recs.get('recommendations', {}).get('recommended_difficulty',
                                                                                  'intermediate')

            # 识别认知薄弱维度
            weak_dimensions = self._identify_weak_cognitive_dimensions(cognitive_state)

            # 生成练习内容
            exercise = await self._create_cognitive_exercise(
                topic, recommended_difficulty, weak_dimensions, learning_params, overall_level
            )

            return {
                "success": True,
                "type": "cognitive",
                "exercise": exercise,
                "cognitive_basis": {
                    "user_level": overall_level,
                    "recommended_difficulty": recommended_difficulty,
                    "weak_dimensions": weak_dimensions,
                    "learning_parameters": learning_params
                }
            }

        except Exception as e:
            logger.error(f"生成认知练习失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "exercise": self._get_fallback_exercise(topic)
            }

    def _identify_weak_cognitive_dimensions(self, cognitive_state: Dict[str, Any]) -> List[str]:
        """识别薄弱的认知维度"""
        dimensions = cognitive_state.get("cognitive_dimensions", {})
        weak_threshold = 0.6

        weak_dims = []
        for dim, score in dimensions.items():
            if score < weak_threshold:
                weak_dims.append(dim)

        # 返回最弱的两个维度
        return sorted(weak_dims, key=lambda x: dimensions[x])[:2]

    async def _create_cognitive_exercise(self, topic: str, difficulty: str,
                                         weak_dimensions: List[str],
                                         learning_params: Dict[str, Any],
                                         user_level: float) -> Dict[str, Any]:
        """创建基于认知科学的练习 - 返回结构化练习题目"""

        # 基于薄弱认知维度设计练习重点
        dimension_focus = self._map_dimensions_to_exercise_focus(weak_dimensions)

        # 基于学习参数调整练习复杂度
        parameters = learning_params.get("parameters", {})
        example_complexity = parameters.get("example_complexity", 0.5)
        scaffolding_level = parameters.get("conceptual_scaffolding", 0.5)

        system_prompt = """你是一个编程教育专家，擅长设计针对特定认知维度训练的编程练习。你需要结合主代理给你的要求和以下信息设计编程练习题目：
- 学习主题：{topic}
- 难度级别：{difficulty}  
- 用户认知水平：{user_level}
- 认知训练重点：{dimension_focus}
- 示例复杂度：{example_complexity}
- 脚手架支持：{scaffolding_level}

请设计一个能够有效训练这些认知维度的编程练习题目，返回格式如下：

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

难度：{difficulty}
主题：{topic}""".format(
            topic=topic or '编程基础',
            difficulty=difficulty,
            user_level=user_level,
            dimension_focus=', '.join(dimension_focus),
            example_complexity=example_complexity,
            scaffolding_level=scaffolding_level
        )

        user_message = """请生成一个关于{topic}的编程练习，要求：

1. 难度适合{difficulty}水平的学习者
2. 特别注重训练以下认知能力：{dimension_focus}
3. 提供清晰的题目描述和具体要求
4. 给出示例输入输出
5. 根据复杂度设置({example_complexity})调整题目难度
6. 根据脚手架支持({scaffolding_level})提供适当的提示

请确保题目能够有效提升目标认知维度。""".format(
            topic=topic or '编程',
            difficulty=difficulty,
            dimension_focus=', '.join(dimension_focus),
            example_complexity=example_complexity,
            scaffolding_level=scaffolding_level
        )

        generated_content = await llm_client.generate_response(system_prompt, user_message)

        # 解析生成的练习内容
        exercise_data = self._parse_exercise_content(generated_content, topic, difficulty)

        return {
            "type": "cognitive_training",
            "topic": topic or "general",
            "difficulty": difficulty,
            "content": exercise_data,
            "cognitive_focus": weak_dimensions,
            "learning_parameters": parameters,
            "source": "cognitive_enhanced"
        }

    def _parse_exercise_content(self, content: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """解析生成的练习内容"""
        # 尝试提取结构化的练习信息
        lines = content.split('\n')
        title = f"{topic or '编程'}练习"
        description = ""
        requirements = []
        examples = []
        hints = []

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
            elif line.startswith('难度：') or line.startswith('主题：'):
                current_section = None
            elif current_section == 'requirements' and line.startswith(('1.', '2.', '3.', '-', '•')):
                # 清理要求条目
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
            elif current_section == 'description' and not line.startswith(('要求：', '示例：', '提示：')):
                description += " " + line

        # 如果解析失败，使用原始内容作为描述
        if not description:
            description = content[:500]  # 限制长度

        # 确保有基本的要求
        if not requirements:
            requirements = ["完成指定功能", "处理边界条件", "编写清晰的代码"]

        if not examples:
            examples = [{"input": "示例输入", "output": "示例输出"}]

        if not hints:
            hints = ["从简单功能开始", "注意边界条件"]

        return {
            "title": title,
            "description": description,
            "requirements": requirements,
            "difficulty": difficulty,
            "examples": examples,
            "hints": hints,
            "expected_solution": "请根据题目要求实现解决方案"
        }

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

    def _get_fallback_exercise(self, topic: str) -> Dict[str, Any]:
        """获取回退练习"""
        return {
            "type": "fallback",
            "topic": topic or "general",
            "difficulty": "intermediate",
            "content": {
                "title": f"{topic or '编程'}基础练习",
                "description": f"请完成一个关于{topic}的练习：实现一个简单的功能函数。",
                "requirements": [
                    "实现指定功能",
                    "处理边界条件",
                    "编写清晰的代码"
                ],
                "difficulty": "intermediate",
                "examples": [
                    {"input": "示例输入", "output": "示例输出"}
                ],
                "hints": ["从简单功能开始", "注意边界条件"],
                "expected_solution": "参考标准实现"
            },
            "cognitive_focus": ["apply"],
            "source": "fallback"
        }


class AdaptiveQuestionBank:
    """自适应题库管理 - 改进版：优先搜索题库，不足时自动生成"""

    def __init__(self):
        self.question_bank = QuestionBank()
        self.cognition_api = get_scientific_cognitive_api_sync()
        self.cognitive_generator = CognitiveExerciseGenerator()

    async def get_personalized_questions(self, user_id: str, topic: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """获取个性化题目 - 优先题库搜索，不足时自动生成"""

        try:
            # 获取用户认知状态
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
            overall_level = cognitive_state["overall_cognitive_level"]

            # 基于认知水平调整难度
            if overall_level < 0.4:
                difficulty = DifficultyLevel.BEGINNER
            elif overall_level < 0.7:
                difficulty = DifficultyLevel.INTERMEDIATE
            else:
                difficulty = DifficultyLevel.ADVANCED

            # 从题库检索题目
            questions = self.question_bank.get_questions_by_filters(
                topic=topic,
                difficulty=difficulty,
                limit=limit
            )

            result_questions = []

            # 转换题库题目格式
            for q in questions:
                result_questions.append({
                    "id": q.id,
                    "type": q.type.value,
                    "topic": q.topic,
                    "difficulty": q.difficulty.value,
                    "content": {
                        "title": f"题库题目 - {q.topic}",
                        "description": q.content,
                        "requirements": ["完成题目要求"],
                        "difficulty": q.difficulty.value,
                        "answer": q.answer,
                        "hints": q.hints or []
                    },
                    "cognitive_level": overall_level,
                    "personalized": True,
                    "source": "question_bank"
                })

            # 如果题库题目不足，使用认知生成器补充
            if len(result_questions) < limit:
                needed_count = limit - len(result_questions)
                logger.info(f"题库题目不足，需要生成{needed_count}个补充题目")

                for i in range(needed_count):
                    try:
                        # 生成认知练习
                        exercise_result = await self.cognitive_generator.generate_cognitive_exercise(user_id, topic)
                        if exercise_result.get("success", False):
                            exercise = exercise_result["exercise"]
                            result_questions.append({
                                "id": f"generated_{int(time.time())}_{i}",
                                "type": "cognitive",
                                "topic": exercise["topic"],
                                "difficulty": exercise["difficulty"],
                                "content": exercise["content"],
                                "cognitive_level": overall_level,
                                "personalized": True,
                                "source": "ai_generated",
                                "cognitive_focus": exercise.get("cognitive_focus", [])
                            })
                    except Exception as e:
                        logger.error(f"生成补充题目失败: {e}")
                        # 添加回退题目
                        result_questions.append(self._create_fallback_question(topic, difficulty.value, i))

            return result_questions

        except Exception as e:
            logger.error("获取个性化题目失败: {}".format(e))
            return self._get_fallback_questions(topic, limit)

    def _create_fallback_question(self, topic: str, difficulty: str, index: int) -> Dict[str, Any]:
        """创建回退题目"""
        return {
            "id": f"fallback_{index}",
            "type": "coding",
            "topic": topic or "general",
            "difficulty": difficulty,
            "content": {
                "title": f"{topic or '编程'}练习 {index + 1}",
                "description": f"实现一个关于{topic}的功能函数",
                "requirements": [
                    "完成指定功能",
                    "编写测试用例",
                    "确保代码质量"
                ],
                "difficulty": difficulty,
                "examples": [
                    {"input": "测试输入", "output": "期望输出"}
                ],
                "hints": ["从简单实现开始", "考虑边界情况"],
                "expected_solution": "标准解决方案"
            },
            "cognitive_level": 0.5,
            "personalized": False,
            "source": "fallback"
        }

    def _get_fallback_questions(self, topic: str, limit: int) -> List[Dict[str, Any]]:
        """获取回退题目"""
        fallback_questions = []
        for i in range(min(limit, 3)):
            fallback_questions.append(self._create_fallback_question(topic, "intermediate", i))
        return fallback_questions


class QuizGenerator:
    """测验生成器"""

    def __init__(self):
        self.cognition_api = get_scientific_cognitive_api_sync()
        self.question_bank = AdaptiveQuestionBank()

    async def generate_adaptive_quiz(self, user_id: str, topic: str = None) -> Dict[str, Any]:
        """生成自适应测验"""

        try:
            # 获取用户认知状态
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)

            # 获取认知强项弱项分析
            strengths_weaknesses = await self.cognition_api.get_cognitive_strengths_weaknesses(user_id)

            # 基于认知状态确定测验参数
            user_level = cognitive_state["overall_cognitive_level"]
            weak_domains = self._identify_weak_domains(cognitive_state)

            # 确定目标主题
            target_topic = topic or (weak_domains[0] if weak_domains else "python_basics")

            # 根据认知水平确定难度和题目数量
            if user_level < 0.4:
                difficulty = DifficultyLevel.BEGINNER
                question_count = 3
            elif user_level < 0.7:
                difficulty = DifficultyLevel.INTERMEDIATE
                question_count = 5
            else:
                difficulty = DifficultyLevel.ADVANCED
                question_count = 7

            # 获取测验题目
            questions = await self.question_bank.get_personalized_questions(
                user_id, target_topic, question_count
            )

            return {
                "success": True,
                "type": "quiz",
                "topic": target_topic,
                "difficulty": difficulty.value,
                "question_count": question_count,
                "questions": questions,
                "adaptive": True,
                "focus_areas": weak_domains[:2] if weak_domains else [target_topic],
                "cognitive_basis": {
                    "user_level": user_level,
                    "weak_domains": weak_domains,
                    "strengths_weaknesses": strengths_weaknesses
                }
            }

        except Exception as e:
            logger.error("生成自适应测验失败: {}".format(e))
            # 返回基础测验
            questions = await self.question_bank.get_personalized_questions(user_id, topic, 3)
            return {
                "success": False,
                "type": "quiz",
                "topic": topic or "general",
                "difficulty": "intermediate",
                "question_count": len(questions),
                "questions": questions,
                "adaptive": False,
                "focus_areas": [topic or "general"]
            }

    def _identify_weak_domains(self, cognitive_state: Dict[str, Any]) -> List[str]:
        """识别薄弱知识领域"""
        knowledge_domains = cognitive_state.get("knowledge_domains", {})
        weak_threshold = 0.6

        weak_domains = []
        for domain, score in knowledge_domains.items():
            if score < weak_threshold:
                weak_domains.append(domain)

        return weak_domains


class ExerciseGenerationAgent(BaseAgent):
    """练习生成代理 - 科学认知API版本 - 改进版"""

    def __init__(self, personal_agent):
        super().__init__("ExerciseGenerationAgent")
        self.cognitive_generator = CognitiveExerciseGenerator()
        self.question_bank = AdaptiveQuestionBank()
        self.quiz_generator = QuizGenerator()
        self.personal_agent = personal_agent
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def generate_exercise(self, exercise_type: str, user_id: str, topic: str = None) -> Dict[str, Any]:
        """生成练习主入口"""

        self.log_activity("生成练习", {
            "type": exercise_type,
            "user_id": user_id,
            "topic": topic
        })

        if exercise_type == "cognitive":
            # 基于认知科学的个性化练习
            return await self.cognitive_generator.generate_cognitive_exercise(user_id, topic)

        elif exercise_type == "preset":
            # 预设题库练习 - 优先题库，不足时自动生成
            questions = await self.question_bank.get_personalized_questions(user_id, topic, limit=3)
            return {
                "success": True,
                "type": "preset",
                "questions": questions,
                "personalized": True,
                "sources": {
                    "question_bank": len([q for q in questions if q.get("source") == "question_bank"]),
                    "ai_generated": len([q for q in questions if q.get("source") == "ai_generated"]),
                    "fallback": len([q for q in questions if q.get("source") == "fallback"])
                }
            }

        elif exercise_type == "quiz":
            # 生成自适应测验
            return await self.quiz_generator.generate_adaptive_quiz(user_id, topic)

        else:
            return {
                "success": False,
                "error": "不支持的练习类型: {}".format(exercise_type),
                "supported_types": ["cognitive", "preset", "quiz"]
            }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理练习生成请求 - 确保题目内容返回给用户"""

        user_id = request["user_id"]
        content = request["content"]

        # 解析请求参数
        exercise_type = self._parse_exercise_type(content)
        topic = self._parse_topic(content)

        # 生成练习
        result = await self.generate_exercise(exercise_type, user_id, topic)

        # 记录科学认知数据
        await self._record_cognitive_data(user_id, content, result)

        # 记录用户行为
        behavior_data = {
            "user_id": user_id,
            "exercise_type": exercise_type,
            "topic": topic or "general",
            "success": result.get("success", False),
            "personalized": result.get("personalized", False),
            "question_count": self._count_questions(result)
        }
        await self.personal_agent.track_user_behavior(behavior_data)

        # 构建响应 - 确保题目内容包含在响应中
        if result.get("success", False):
            response_msg = self._build_success_response(exercise_type, result)
            response_details = self._build_response_details(result)

            # 将题目内容直接包含在响应中，确保用户能看到
            full_response = response_msg + "\n\n" + self._format_exercises_for_display(result)
        else:
            response_msg = "生成练习失败: {}".format(result.get('error', '未知错误'))
            response_details = {}
            full_response = response_msg

        return {
            "response": full_response,  # 确保包含完整的题目内容
            "details": response_details,
            "success": result.get("success", False)
        }

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
        text += f" | 来源: {exercise_data.get('source', '未知')}"

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
            "personalized": result.get("personalized", False)
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
                'content': content[:500],  # 限制长度
                'user_response': str(result.get('type', 'unknown')),
                'context': '练习生成交互',
                'metadata': {
                    'exercise_type': result.get('type', 'unknown'),
                    'success': result.get('success', False),
                    'personalized': result.get('personalized', False),
                    'topic': result.get('topic', 'general'),
                    'question_count': self._count_questions(result)
                }
            }

            analysis_result = await self.cognition_api.analyze_learning_interaction(user_id, interaction_data)

            if analysis_result['success']:
                self.logger.info("练习生成认知分析完成")

        except Exception as e:
            self.logger.warning("记录认知数据失败: {}".format(e))

    def _parse_exercise_type(self, content: str) -> str:
        """解析练习类型"""
        content_lower = content.lower()

        if "测验" in content_lower or "测试" in content_lower or "quiz" in content_lower:
            return "quiz"
        elif "认知" in content_lower or "个性化" in content_lower:
            return "cognitive"
        else:
            return "preset"  # 默认预设题库

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

    def _build_success_response(self, exercise_type: str, result: Dict[str, Any]) -> str:
        """构建成功响应消息"""

        type_names = {
            "cognitive": "个性化认知练习",
            "preset": "题库练习",
            "quiz": "自适应测验"
        }

        base_msg = "✅ 已生成{}".format(type_names.get(exercise_type, exercise_type))

        # 添加题目数量信息
        question_count = self._count_questions(result)
        base_msg += f"，共{question_count}道题目"

        # 添加来源信息
        if "sources" in result:
            sources = result["sources"]
            source_parts = []
            if sources.get("question_bank", 0) > 0:
                source_parts.append(f"{sources['question_bank']}道来自题库")
            if sources.get("ai_generated", 0) > 0:
                source_parts.append(f"{sources['ai_generated']}道AI生成")
            if sources.get("fallback", 0) > 0:
                source_parts.append(f"{sources['fallback']}道备用题目")

            if source_parts:
                base_msg += "（" + "，".join(source_parts) + "）"

        if "cognitive_basis" in result:
            basis = result["cognitive_basis"]
            level = basis.get("user_level", 0.5)
            weak_dims = basis.get("weak_dimensions", [])

            if weak_dims:
                dim_names = {
                    'remember': '记忆', 'understand': '理解', 'apply': '应用',
                    'analyze': '分析', 'evaluate': '评价', 'create': '创造'
                }
                weak_names = [dim_names.get(dim, dim) for dim in weak_dims]
                base_msg += "，重点训练{}能力".format(', '.join(weak_names))

        return base_msg